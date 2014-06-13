"""
Verifies trigger data-sanity
"""
from datetime import datetime, date, timedelta, time
from decimal import Decimal
import os
try:
    import unittest2 as unittest
except ImportError:
    import unittest
import random

from ddt import ddt, data
from six.moves import range
from testconfig import config
from sqlalchemy import create_engine, MetaData, and_
from sqlalchemy.dialects.postgres import \
    TIME, TIMESTAMP, DATE, INTEGER, BOOLEAN, DOUBLE_PRECISION, \
    NUMERIC, VARCHAR, TEXT, BYTEA


ECHO = False

alphabet = u'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789/&='
alphabetws = alphabet + u' \n'

value_generator = {
    DATE: lambda: date(random.randint(1970, 2014),
                       random.randint(1, 12),
                       random.randint(1, 28)),
    TIMESTAMP: lambda: datetime(random.randint(1970, 2014),
                                random.randint(1, 12),
                                random.randint(1, 28),
                                random.randint(0, 23),
                                random.randint(0, 59),
                                random.randint(0, 59),
                                random.randint(0, 1000000 - 1)),
    TIME: lambda: time(random.randint(0, 23),
                       random.randint(0, 59)),
    INTEGER: lambda: random.randint(0, 1000000),
    BOOLEAN: lambda: random.choice([False, True]),
    DOUBLE_PRECISION: lambda: random.uniform(0.0000, 1000000.0000),
    NUMERIC: lambda: Decimal(random.uniform(0.0000, 1000000.0000)),
    VARCHAR: lambda: ''.join([random.choice(alphabet) for _ in range(32)]),
    TEXT: lambda: ''.join([random.choice(alphabetws) for _ in range(100)]),
    BYTEA: lambda: os.urandom(1024),
}


def populate(conn, table, overrides={}, id=None):
    """
    Recursively populates a table, and its depencies
    Returns it id
    """
    values = {}
    for column in table.c:
        # Use overrides if specified
        dotted_name = '.'.join([table.name, column.name])
        if dotted_name in overrides:
            values[column.name] = overrides[dotted_name]
        # Don't assign if already assigned by a look-ahead
        if column.name in values:
            continue
        # Ignore these columns:
        if column.name == 'id':
            continue
        # Recursively traverse to dependent tables
        if column.foreign_keys:
            dep_table = list(column.foreign_keys)[0].column.table
            values[column.name] = populate(conn, dep_table, overrides)[0]

        # Otherwise assign random scalar
        else:
            # Before-hand exceptions:
            # Exception for create_date <= modify_date
            if column.name == 'modify_date':
                values.setdefault('create_date', value_generator[TIMESTAMP]())
                values[column.name] = values['create_date'] + timedelta(1)
                continue
            try:
                values[column.name] = value_generator[column.type.__class__]()
            except KeyError as e:
                raise Exception('Cannot generate value for %s because: %s'
                                % (dotted_name, str(e)))

    if not id:
        result = conn.execute(table.insert(values))
        return result.inserted_primary_key
    else:
        result = conn.execute(
            table
            .update()
            .where(and_(*[c == i for c, i in zip(table.primary_key.columns,
                                                 id)]))
            .values(**values))
        if len(table.primary_key.columns) > 1:
            return [values[c.name] for c in table.primary_key.columns]
        else:
            return id


def truncate_all(conn):
    # Cleanup the databaes before we begin (expensive)
    with conn.begin():
        conn.execute('TRUNCATE "user" CASCADE')


@ddt
class TestTrigger(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._src_engine = create_engine(config['src'], echo=ECHO)
        cls._dst_engine = create_engine(config['dst'], echo=ECHO)
        cls.src_conn = cls._src_engine.connect()
        cls.dst_conn = cls._dst_engine.connect()
        cls.src_metadata = MetaData(bind=cls._src_engine)
        cls.src_metadata.reflect()
        cls.dst_metadata = MetaData(bind=cls._dst_engine)
        cls.dst_metadata.reflect()

        # CLEAN THE DATABASE OF PREVIOUS RUNS/ERRORS/MODIFICATIONS/ETC
        truncate_all(cls.src_conn)
        truncate_all(cls.dst_conn)

        # Add because we truncated all tables...
        with cls.dst_conn.begin():
            for state in ('complete', 'pending-review', 'pending-entry'):
                populate(cls.dst_conn, cls.dst_metadata.tables['state'],
                         overrides={'state.name': state})

    def _getRecord(self, src_table, src_id, dst_table=None):
        if dst_table is None:
            if src_table.name in set(['text', 'blob', 'integer', 'datetime',
                                      'decimal', 'string', 'object']):
                dst_table = self.dst_metadata.tables['value_' + src_table.name]
            else:
                dst_table = self.dst_metadata.tables[src_table.name]

        src_data = (
            self.src_conn.execute(
                src_table.select()
                .where(and_(*[c == i
                            for c, i in zip(src_table.primary_key.columns,
                                            src_id)])))
            .fetchone())

        if src_data is None:
            return None, None

        # One-to-many, one-to-one
        if src_table.name == 'user':
            dst_data = (
                self.dst_conn.execute(
                    dst_table.select()
                    .where(dst_table.c.key == src_data['key']))
                .fetchone())

        elif dst_table.name == 'patient':
            dst_data = (
                self.dst_conn.execute(
                    dst_table.select()
                    .where(dst_table.c.zid == src_data['zid']))
                .fetchone())

        elif len(src_table.primary_key.columns) < 2:
            dst_data = (
                self.dst_conn.execute(
                    dst_table.select()
                    .where(
                        (dst_table.c.old_db == src_table.bind.url.database) &
                        (dst_table.c.old_id == src_id[0])))
                .fetchone())
        # Many-to-many
        else:
            dst_ids = []
            for column, id in zip(src_table.primary_key, src_id):
                dep_table = list(column.foreign_keys)[0].column.table
                _, dst_data = self._getRecord(dep_table, [id])
                dst_ids.append(dst_data['id'])
            dst_data = (
                self.dst_conn.execute(
                    dst_table.select()
                    .where(and_(*[c == i
                                for c, i in zip(dst_table.primary_key.columns,
                                                dst_ids)])))
                .fetchone())

        return src_data, dst_data

    def assertRecordEqual(self, src_table, src_data, dst_table, dst_data,
                          ignore=[]):
        invalid_fields = []

        assert src_data is not None
        assert dst_data is not None

        ignore = set(ignore or [])

        for column in src_table.c:
            if column.name == 'id':
                continue
            if '.'.join([src_table.name, column.name]) in ignore:
                continue

            src_val = src_data[column.name]
            dst_val = dst_data[column.name] \
                if column.name in dst_data else None

            # State is an FK in the new system
            if src_table.name == 'entity' and column.name == 'state':
                dst_state_table = self.dst_metadata.tables['state']
                dst_state_data = (
                    self.dst_conn.execute(
                        dst_state_table.select()
                        .where(dst_state_table.c.id == dst_data['state_id']))
                    .fetchone())
                dst_val = dst_state_data['name']

            # Derefence all other FKs
            elif column.foreign_keys and src_val is not None:
                src_dep_table = list(column.foreign_keys)[0].column.table
                src_dep_data, dst_dep_data = \
                    self._getRecord(src_dep_table, [src_val])
                if src_dep_table.name == 'user':
                    src_val = src_dep_data['key']
                    dst_val = dst_dep_data['key']
                elif src_dep_table.name == 'patient':
                    src_val = src_dep_data['our']
                    dst_val = dst_dep_data['our']
                else:
                    dst_val = dst_dep_data['old_id']

            if (src_table.name == 'entity'
                    and column.name == 'state'
                    and src_val in ('not-done', 'not-applicable')
                    and dst_val != 'complete'):
                invalid_fields.append(
                    '%s.%s: %s not forwarded to %s'
                    % (src_table.name, column.name, src_val, dst_val))

            elif src_val != dst_val:
                invalid_fields.append(
                    '%s.%s: %s != %s'
                    % (src_table.name, column.name, src_val, dst_val))

        if invalid_fields:
            raise AssertionError('\n'.join(invalid_fields))

    @data(
        'aliquot',
        'aliquotstate',
        'aliquottype',
        'location',
        'specialinstruction',
        'specimen',
        'specimenstate',
        'specimentype',

        'arm',
        'category',
        'cycle',
        'enrollment',
        'partner',
        'patient',
        'patientreference',
        'reftype',
        'site',
        'stratum',
        'study',
        'visit',

        'schema',
        'attribute',
        'blob',
        'datetime',
        'decimal',
        'entity',
        'integer',
        'string',
        'text',
        'user',

        'schema_category',
        'site_lab_location',
        'specimentype_cycle',
        'specimentype_study',
        'visit_cycle'
    )
    def test_direct_track(self, table):
        """
        It should be able to directly transfer data to non-upgraded tables
        """
        src_table = self.src_metadata.tables[table]
        dst_table = self.src_metadata.tables[table]
        overrides = {
            'entity.state': 'complete',
            'schema.state': 'published',
            'schema.storage': 'eav',
            'schema.is_inline': False,
            'schema.base_schema_id': None,
            'attribute.type': 'string',
            'attribute.is_collection': True,
            'attribute.object_schema_id': None,
            'attribute.value_min': random.randint(0, 9),
            'attribute.value_max': random.randint(10, 19),
            'attribute.collection_min': random.randint(0, 9),
            'attribute.collection_max': random.randint(10, 19),
            'choice.value': ''.join([str(random.choice(range(10)))
                                     for _ in range(8)]),
            'string.choice_id': None}

        # Inserts
        with self.src_conn.begin():
            src_id = populate(self.src_conn, src_table, overrides=overrides)
        src_data, dst_data = self._getRecord(src_table, src_id)
        self.assertRecordEqual(src_table, src_data, dst_table, dst_data,
                               ignore=['schema.state',
                                       'schema.is_inline',
                                       'entity.state'])

        # Updates
        with self.src_conn.begin():
            src_id = populate(self.src_conn, src_table,
                              overrides=overrides, id=src_id)
        src_data, dst_data = self._getRecord(src_table, src_id)
        self.assertRecordEqual(src_table, src_data, dst_table, dst_data,
                               ignore=['schema.state',
                                       'schema.is_inline',
                                       'entity.state'])

        # Deletes
        self.src_conn.execute(
            src_table.delete()
            .where(and_(*[c == i for c, i in zip(src_table.primary_key.columns,
                                                 src_id)])))
        src_data, dst_data = self._getRecord(src_table, src_id)
        self.assertIsNone(src_data)
        self.assertIsNone(dst_data)

    @data('complete', 'pending-entry', 'pending-review')
    def test_state_supported(self, state):
        """
        It should properly transfer supported state data
        """
        src_table = self.src_metadata.tables['entity']
        dst_table = self.dst_metadata.tables['entity']

        overrides = {
            'entity.state': state,
            'schema.state': 'published',
            'schema.storage': 'eav',
            'schema.is_inline': False,
            'schema.base_schema_id': None,
        }

        # Inserts
        with self.src_conn.begin():
            src_id = populate(self.src_conn, src_table, overrides=overrides)
        src_data, dst_data = self._getRecord(src_table, src_id)
        self.assertRecordEqual(src_table, src_data, dst_table, dst_data)
        self.assertFalse(dst_data['is_null'])

        # Updates
        with self.src_conn.begin():
            src_id = populate(self.src_conn, src_table,
                              overrides=overrides, id=src_id)
        src_data, dst_data = self._getRecord(src_table, src_id)
        self.assertRecordEqual(src_table, src_data, dst_table, dst_data)
        self.assertFalse(dst_data['is_null'])

        # Deletes
        self.src_conn.execute(
            src_table.delete()
            .where(and_(*[c == i for c, i in zip(src_table.primary_key.columns,
                                                 src_id)])))
        src_data, dst_data = self._getRecord(src_table, src_id)
        self.assertIsNone(src_data)
        self.assertIsNone(dst_data)

    @data('not-applicable', 'not-done')
    def test_is_null(self, state):
        """
        It should set is_null/complete when using not applicable/done
        """
        src_table = self.src_metadata.tables['entity']
        dst_table = self.dst_metadata.tables['entity']

        overrides = {
            'entity.state': state,
            'schema.state': 'published',
            'schema.storage': 'eav',
            'schema.is_inline': False,
            'schema.base_schema_id': None,
        }

        # Inserts
        with self.src_conn.begin():
            src_id = populate(self.src_conn, src_table, overrides=overrides)
        src_data, dst_data = self._getRecord(src_table, src_id)
        self.assertTrue(dst_data['is_null'])

        # Updates
        with self.src_conn.begin():
            src_id = populate(self.src_conn, src_table,
                              overrides=overrides, id=src_id)
        src_data, dst_data = self._getRecord(src_table, src_id)
        self.assertTrue(dst_data['is_null'])

    @data('patient', 'enrollment', 'visit', 'stratum')
    def test_context(self, external):
        """
        It should properly align context values
        """
        src_ext_table = self.src_metadata.tables[external]
        src_table = self.src_metadata.tables['context']
        dst_table = self.dst_metadata.tables['context']
        overrides = {
            'context.external': external,
            'entity.state': 'complete',
            'schema.state': 'published',
            'schema.storage': 'eav',
            'schema.is_inline': False,
            'schema.base_schema_id': None}

        # Inserts
        with self.src_conn.begin():
            src_ext_id = populate(self.src_conn, src_ext_table)
            overrides['context.key'] = src_ext_id[0]
            src_id = populate(self.src_conn, src_table, overrides=overrides)
        src_data, dst_data = self._getRecord(src_table, src_id)
        src_data = dict(src_data.items())
        dst_data = dict(dst_data.items())
        src_ext_data, dst_ext_data = self._getRecord(src_ext_table, src_ext_id)
        if external == 'user':
            src_data['key'] = src_ext_data['our']
            dst_data['key'] = src_ext_data['our']
        else:
            dst_data['key'] = src_ext_data['id']
        self.assertRecordEqual(src_table, src_data, dst_table, dst_data)

        # Updates
        with self.src_conn.begin():
            src_ext_id = populate(self.src_conn, src_ext_table)
            overrides['context.key'] = src_ext_id[0]
            src_id = populate(self.src_conn, src_table,
                              overrides=overrides, id=src_id)
        src_data, dst_data = self._getRecord(src_table, src_id)
        src_data = dict(src_data.items())
        dst_data = dict(dst_data.items())
        src_ext_data, dst_ext_data = self._getRecord(src_ext_table, src_ext_id)
        if external == 'user':
            src_data['key'] = src_ext_data['our']
            dst_data['key'] = src_ext_data['our']
        else:
            dst_data['key'] = src_ext_data['id']
        self.assertRecordEqual(src_table, src_data, dst_table, dst_data)

        # Deletes
        self.src_conn.execute(
            src_table.delete()
            .where(and_(*[c == i for c, i in zip(src_table.primary_key.columns,
                                                 src_id)])))
        src_data, dst_data = self._getRecord(src_table, src_id)
        self.assertIsNone(src_data)
        self.assertIsNone(dst_data)

    def test_value_choice(self):
        """
        It should redirect string choices to the value_choice table
        """
        src_choice_table = self.src_metadata.tables['choice']
        src_table = self.src_metadata.tables['string']
        dst_table = self.dst_metadata.tables['value_choice']
        overrides = {
            'entity.state': 'complete',
            'schema.state': 'published',
            'schema.storage': 'eav',
            'schema.is_inline': False,
            'schema.base_schema_id': None,
            'attribute.type': 'string',
            'attribute.is_collection': True,
            'attribute.object_schema_id': None,
            'attribute.value_min': None,
            'attribute.value_max': None,
            'attribute.collection_min': None,
            'attribute.collection_max': None}

        # Inserts
        with self.src_conn.begin():
            overrides['choice.value'] = value_generator[INTEGER]()
            src_choice_id = populate(self.src_conn, src_choice_table,
                                     overrides=overrides)
            overrides['string.choice_id'] = src_choice_id[0]
            overrides['string.value'] = overrides['choice.value']
            src_id = populate(self.src_conn, src_table, overrides=overrides)
        src_data, dst_data = self._getRecord(src_table, src_id, dst_table)
        dst_data = dict(dst_data.items())
        dst_data['choice_id'] = dst_data['value']
        self.assertRecordEqual(src_table, src_data, dst_table, dst_data,
                               ignore=['string.value'])

        # Updates
        with self.src_conn.begin():
            overrides['choice.value'] = value_generator[INTEGER]()
            src_choice_id = populate(self.src_conn, src_choice_table,
                                     overrides=overrides)
            overrides['string.choice_id'] = src_choice_id[0]
            src_id = populate(self.src_conn, src_table,
                              overrides=overrides, id=src_id)
        src_data, dst_data = self._getRecord(src_table, src_id, dst_table)
        dst_data = dict(dst_data.items())
        dst_data['choice_id'] = dst_data['value']
        self.assertRecordEqual(src_table, src_data, dst_table, dst_data,
                               ignore=['string.value'])

        # Deletes
        self.src_conn.execute(
            src_table.delete()
            .where(and_(*[c == i for c, i in zip(src_table.primary_key.columns,
                                                 src_id)])))
        src_data, dst_data = self._getRecord(src_table, src_id, dst_table)
        self.assertIsNone(src_data)
        self.assertIsNone(dst_data)

    def test_section(self):
        """
        It should direct parent-attribtes to sections
        """
        src_schema_table = self.src_metadata.tables['schema']
        src_attr_table = self.src_metadata.tables['attribute']
        src_user_table = self.src_metadata.tables['user']

        dst_attr_table = self.dst_metadata.tables['attribute']
        dst_sect_table = self.dst_metadata.tables['section']
        dst_sectattr_table = self.dst_metadata.tables['section_attribute']

        # Ignore these in the parent attribute as they aren't copied to a
        # section
        src_pattr_ignore = [
            'attribute.type',
            'attribute.checksum',
            'attribute.is_collection',
            'attribute.is_required',
            'attribute.object_schema_id',
            'attribute.value_min',
            'attribute.value_max',
            'attribute.collection_min',
            'attribute.collection_max',
            'attribute.validator']

        # Inserts
        with self.src_conn.begin():
            src_user_id, = self.src_conn.execute(
                src_user_table.insert().values(key=value_generator[VARCHAR]())
                ).inserted_primary_key
            src_pschema_id, = self.src_conn.execute(
                src_schema_table.insert()
                .values(
                    name=value_generator[VARCHAR](),
                    title=value_generator[VARCHAR](),
                    is_inline=False,
                    create_user_id=src_user_id,
                    modify_user_id=src_user_id,
                    revision=1)
                ).inserted_primary_key
            src_cschema_id, = self.src_conn.execute(
                src_schema_table.insert()
                .values(
                    name=value_generator[VARCHAR](),
                    title='',
                    is_inline=True,
                    create_user_id=src_user_id,
                    modify_user_id=src_user_id,
                    revision=1)
                ).inserted_primary_key
            src_pattr_id, = self.src_conn.execute(
                src_attr_table.insert()
                .values(
                    schema_id=src_pschema_id,
                    name=value_generator[VARCHAR](),
                    title=value_generator[VARCHAR](),
                    description=value_generator[VARCHAR](),
                    type='object',
                    checksum='',
                    is_collection=False,
                    is_required=True,
                    object_schema_id=src_cschema_id,
                    order=0,
                    create_user_id=src_user_id,
                    modify_user_id=src_user_id,
                    revision=1)
                ).inserted_primary_key
            src_cattr_id, = self.src_conn.execute(
                src_attr_table.insert()
                .values(
                    schema_id=src_cschema_id,
                    name=value_generator[VARCHAR](),
                    title=value_generator[VARCHAR](),
                    type='string',
                    checksum='',
                    is_collection=False,
                    is_required=True,
                    order=0,
                    create_user_id=src_user_id,
                    modify_user_id=src_user_id,
                    revision=1)
                ).inserted_primary_key
        # Make sure parent attribute -> section
        src_pattr_data = self.src_conn.execute(
            src_attr_table.select().where(
                src_attr_table.c.id == src_pattr_id)
            ).fetchone()
        dst_sect_data = self.dst_conn.execute(
            dst_sect_table.select().where(
                dst_sect_table.c.old_id == src_pattr_id)
            ).fetchone()
        self.assertRecordEqual(src_attr_table, src_pattr_data,
                               dst_sect_table, dst_sect_data,
                               ignore=src_pattr_ignore)
        # Sub-attributes will be listed in the join table
        dst_attr_data = self.dst_conn.execute(
            dst_attr_table.select().where(
                dst_attr_table.c.old_id == src_cattr_id)
            ).fetchone()
        dst_sa_data = self.dst_conn.execute(
            dst_sectattr_table.select().where(
                (dst_sectattr_table.c.section_id == dst_sect_data['id']) &
                (dst_sectattr_table.c.attribute_id == dst_attr_data['id']))
            ).fetchone()
        self.assertIsNotNone(dst_sa_data)

        # Now "move" the sub-attribute to a new child schema (i.e. section)
        with self.src_conn.begin():
            src_cschema_id, = self.src_conn.execute(
                src_schema_table.insert()
                .values(
                    name=value_generator[VARCHAR](),
                    title='',
                    description=value_generator[VARCHAR](),
                    is_inline=True,
                    create_user_id=src_user_id,
                    modify_user_id=src_user_id,
                    revision=1)
                ).inserted_primary_key
            src_pattr_id, = self.src_conn.execute(
                src_attr_table.insert()
                .values(
                    schema_id=src_pschema_id,
                    name=value_generator[VARCHAR](),
                    title=value_generator[VARCHAR](),
                    description=value_generator[VARCHAR](),
                    type='object',
                    checksum='',
                    is_collection=False,
                    is_required=True,
                    object_schema_id=src_cschema_id,
                    order=1,
                    create_user_id=src_user_id,
                    modify_user_id=src_user_id,
                    revision=1)
                ).inserted_primary_key
            self.src_conn.execute(
                src_attr_table.update()
                .where(src_attr_table.c.id == src_cattr_id)
                .values(schema_id=src_cschema_id))
        dst_attr_data = self.dst_conn.execute(
            dst_attr_table.select().where(
                dst_attr_table.c.old_id == src_cattr_id)
            ).fetchone()
        dst_sect_data = self.dst_conn.execute(
            dst_sect_table.select().where(
                dst_sect_table.c.old_id == src_pattr_id)
            ).fetchone()
        dst_sa_data = self.dst_conn.execute(
            dst_sectattr_table.select().where(
                (dst_sectattr_table.c.section_id == dst_sect_data['id']) &
                (dst_sectattr_table.c.attribute_id == dst_attr_data['id']))
            ).fetchone()
        self.assertIsNotNone(dst_sa_data)

        # Update the actual parent attribute (which should update the section)
        with self.src_conn.begin():
            self.src_conn.execute(
                src_attr_table.update()
                .where(src_attr_table.c.id == src_pattr_id)
                .values(
                    title=value_generator[VARCHAR](),
                    description=value_generator[VARCHAR]()))
        src_pattr_data = self.src_conn.execute(
            src_attr_table.select().where(
                src_attr_table.c.id == src_pattr_id)
            ).fetchone()
        dst_sect_data = self.dst_conn.execute(
            dst_sect_table.select().where(
                dst_sect_table.c.old_id == src_pattr_id)
            ).fetchone()
        self.assertRecordEqual(src_attr_table, src_pattr_data,
                               dst_sect_table, dst_sect_data,
                               ignore=src_pattr_ignore)

        # Delete the parent attribute
        with self.src_conn.begin():
            self.src_conn.execute(
                src_attr_table.delete()
                .where(src_attr_table.c.id == src_pattr_id))
        dst_sect_data = self.dst_conn.execute(
            dst_sect_table.select().where(
                dst_sect_table.c.old_id == src_pattr_id)
            ).fetchone()
        dst_attr_data = self.dst_conn.execute(
            dst_attr_table.select().where(
                dst_sect_table.c.old_id == src_cattr_id)
            ).fetchone()
        self.assertIsNone(dst_sect_data)
        self.assertIsNone(dst_attr_data)

    @data('string', 'integer', 'decimal', 'datetime', 'blob', 'text')
    def test_sub_value(self, type):
        """
        It should be able to keep sub-values/attributes flattened in the new
        system
        """
        src_schema_table = self.src_metadata.tables['schema']
        src_attr_table = self.src_metadata.tables['attribute']
        src_user_table = self.src_metadata.tables['user']
        src_entity_table = self.src_metadata.tables['entity']
        src_object_table = self.src_metadata.tables['object']
        src_value_table = self.src_metadata.tables[type]

        dst_schema_table = self.dst_metadata.tables['schema']
        dst_attr_table = self.dst_metadata.tables['attribute']
        dst_entity_table = self.dst_metadata.tables['entity']
        dst_value_table = self.dst_metadata.tables['value_' + type]

        # Inserts
        with self.src_conn.begin():
            src_user_id, = self.src_conn.execute(
                src_user_table.insert().values(key=value_generator[VARCHAR]())
                ).inserted_primary_key
            src_pschema_id, = self.src_conn.execute(
                src_schema_table.insert()
                .values(
                    name=value_generator[VARCHAR](),
                    title=value_generator[VARCHAR](),
                    is_inline=False,
                    create_user_id=src_user_id,
                    modify_user_id=src_user_id,
                    revision=1)
                ).inserted_primary_key
            src_cschema_id, = self.src_conn.execute(
                src_schema_table.insert()
                .values(
                    name=value_generator[VARCHAR](),
                    title=value_generator[VARCHAR](),
                    is_inline=True,
                    create_user_id=src_user_id,
                    modify_user_id=src_user_id,
                    revision=1)
                ).inserted_primary_key
            src_pattr_id, = self.src_conn.execute(
                src_attr_table.insert()
                .values(
                    schema_id=src_pschema_id,
                    name=value_generator[VARCHAR](),
                    title=value_generator[VARCHAR](),
                    description=value_generator[VARCHAR](),
                    type='object',
                    checksum=value_generator[VARCHAR](),
                    is_collection=False,
                    is_required=True,
                    object_schema_id=src_cschema_id,
                    order=0,
                    create_user_id=src_user_id,
                    modify_user_id=src_user_id,
                    revision=1)
                ).inserted_primary_key
            src_cattr_id, = self.src_conn.execute(
                src_attr_table.insert()
                .values(
                    schema_id=src_cschema_id,
                    name=value_generator[VARCHAR](),
                    title=value_generator[VARCHAR](),
                    type=type,
                    checksum='',
                    is_collection=False,
                    is_required=True,
                    order=0,
                    create_user_id=src_user_id,
                    modify_user_id=src_user_id,
                    revision=1)
                ).inserted_primary_key
            src_pentity_id, = self.src_conn.execute(
                src_entity_table.insert()
                .values(
                    schema_id=src_pschema_id,
                    name=value_generator[VARCHAR](),
                    title=value_generator[VARCHAR](),
                    collect_date=value_generator[DATE](),
                    create_user_id=src_user_id,
                    modify_user_id=src_user_id,
                    revision=1)
                ).inserted_primary_key
            src_centity_id, = self.src_conn.execute(
                src_entity_table.insert()
                .values(
                    schema_id=src_cschema_id,
                    name=value_generator[VARCHAR](),
                    title=value_generator[VARCHAR](),
                    collect_date=value_generator[DATE](),
                    create_user_id=src_user_id,
                    modify_user_id=src_user_id,
                    revision=1)
                ).inserted_primary_key
            src_object_id, = self.src_conn.execute(
                src_object_table.insert()
                .values(
                    entity_id=src_pentity_id,
                    attribute_id=src_pattr_id,
                    value=src_centity_id,
                    create_user_id=src_user_id,
                    modify_user_id=src_user_id,
                    revision=1)
                ).inserted_primary_key
            src_value_id, = self.src_conn.execute(
                src_value_table.insert()
                .values(
                    entity_id=src_centity_id,
                    attribute_id=src_cattr_id,
                    value=value_generator[
                        src_value_table.c.value.type.__class__](),
                    create_user_id=src_user_id,
                    modify_user_id=src_user_id,
                    revision=1)
                ).inserted_primary_key
        # Ensure schema is still flat on the new system
        dst_pschema_data = self.dst_conn.execute(
            dst_schema_table.select().where(
                dst_schema_table.c.old_id == src_pschema_id)
            ).fetchone()
        dst_cattr_data = self.dst_conn.execute(
            dst_attr_table.select().where(
                dst_attr_table.c.old_id == src_cattr_id)
            ).fetchone()
        self.assertEqual(dst_pschema_data['id'],
                         dst_cattr_data['schema_id'])

        # Ensure the data is still flat in the new system
        dst_entity_data = self.dst_conn.execute(
            dst_entity_table.select().where(
                dst_entity_table.c.old_id == src_pentity_id)
            ).fetchone()
        dst_value_data = self.dst_conn.execute(
            dst_value_table.select().where(
                dst_value_table.c.old_id == src_value_id)
            ).fetchone()
        self.assertEqual(dst_entity_data['id'],
                         dst_value_data['entity_id'])
