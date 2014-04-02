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


@ddt
class TestTrigger(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.src_engine = create_engine(config['src'], echo=ECHO)
        cls.dst_engine = create_engine(config['dst'], echo=ECHO)
        cls.src_conn = cls.src_engine.connect()
        cls.dst_conn = cls.dst_engine.connect()
        cls.src_metadata = MetaData(bind=cls.src_engine)
        cls.src_metadata.reflect()
        cls.dst_metadata = MetaData(bind=cls.dst_engine)
        cls.dst_metadata.reflect()

        # Cleanup the databaes before we begin (expensive)
        for conn in (cls.src_conn, cls.dst_conn):
            with conn.begin():
                conn.execute('TRUNCATE "user" CASCADE')

    def _getRecord(self, src_table, src_id):
        if src_table.name in set(['text', 'blob', 'integer', 'datetime',
                                  'decimal', 'string', 'object']):
            dst_table = self.dst_metadata.tables['value_' + src_table.name]
        else:
            dst_table = self.dst_metadata.tables[src_table.name]

        src_data = (
            self.src_engine.execute(
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
                self.dst_engine.execute(
                    dst_table.select()
                    .where(dst_table.c.key == src_data['key']))
                .fetchone())

        elif dst_table.name == 'patient':
            dst_data = (
                self.dst_engine.execute(
                    dst_table.select()
                    .where(dst_table.c.zid == src_data['zid']))
                .fetchone())

        elif len(src_table.primary_key.columns) < 2:
            dst_data = (
                self.dst_engine.execute(
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
                self.dst_engine.execute(
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

            if column.foreign_keys and src_val is not None:
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

            if src_val != dst_val:
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
        with self.src_engine.begin() as conn:
            src_id = populate(conn, src_table, overrides=overrides)
        src_data, dst_data = self._getRecord(src_table, src_id)
        self.assertRecordEqual(src_table, src_data, dst_table, dst_data,
                               ignore=['schema.state',
                                       'schema.is_inline',
                                       'entity.state'])

        # Updates
        with self.src_engine.begin() as conn:
            src_id = populate(conn, src_table, overrides=overrides, id=src_id)
        src_data, dst_data = self._getRecord(src_table, src_id)
        self.assertRecordEqual(src_table, src_data, dst_table, dst_data,
                               ignore=['schema.state',
                                       'schema.is_inline',
                                       'entity.state'])

        # Deletes
        self.src_conn.execute(
            src_table.delete()
            .where(and_(*[c == i for c, i in zip(dst_table.primary_key.columns,
                                                 src_id)])))
        src_data, dst_data = self._getRecord(src_table, src_id)
        self.assertIsNone(src_data)
        self.assertIsNone(dst_data)

    #def test_sub_objects(self):
        #pass

    #def test_attribute(self):
        #pass

    #def test_section(self):
        #pass

    #def test_context(self):
        #pass

    #def test_choice(self):
        #pass
