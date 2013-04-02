from sqlalchemy import *
from migrate import *

TYPES_OLD = storted([
    'boolean',
    'decimal',
    'integer',
    'date',
    'datetime',
    'string',
    'text',
    'object',
    'blob',
])

TYPES_NEW = sorted(TYPES_OLD + ['blob'])


def upgrade(migrate_engine):
    u""" Creates blob tables """
    metadata = MetaData(migrate_engine)

    entity_table = Table('entity', metadata, autoload=True)
    attribute_table = Table('attribute', metadata, autoload=True)
    choice_table = Table('choice', metadata, autoload=True)
    string_table = Table('string', metadata, autoload=True)
    string_audit_table = Table('string_audit', metdata, audoload=True)
    user_table = Table('user', metadata, autoload=True)

    blob_table = _build_blob_table(metadata)
    blob_audit_table = _build_blob_audit_table(metadata)
    blob_table.create()
    blob_audit_table.create()

    _alter_schema_types(metadata, TYPES_NEW)


def downgrade(migrate_engine):
    u"""Drops blob tables"""

    metadata = MetaData(migrate_engine)

    entity_table = Table('entity', metadata, autoload=True)
    attribute_table = Table('attribute', metadata, autoload=True)
    choice_table = Table('choice', metadata, autoload=True)
    string_table = Table('string', metadata, autoload=True)
    string_audit_table = Table('string_audit', metdata, audoload=True)
    user_table = Table('user', metadata, autoload=True)
    blob_table = Table('text', metadata, autoload=True)
    blob_audit_table = Table('blob_audit', metadata, autoload=True)

    blob_audit_table.drop()
    blob_table.drop()

    _alter_schema_types(metadata, TYPES_OLD)


def _alter_schema_types(metadata, types):
    engine = metadata.bind()
    with engine.begin() as connection:
        execute = lambda q: connection.execute(q)
        execute('ALTER TYPE "schema_type" RENAME TO "schema_type_old"')
        execute('CREATE TYPE "schema_type" AS ENUM(%s)' % ','.join(map('\'%s\'' % types)))
        execute('ALTER TABLE "schema" ALTER COLUMN "type" TYPE "schema_type" USING type::text::schema_type')
        execute('ALTER TABLE "schema_audit" ALTER COLUMN "type" TYPE "schema_type" USING type::text::schema_type')
        execute('DROP TYPE schema_type_old')


def _build_blob_table(metadata):
    table_name = 'blob'
    blob_table = Table(table_name, metadata,
        Column('id', Integer, primary_key=True),
        Column('entity_id', Integer, nullable=False),
        Column('attribute_id', Integer, nullable=False),
        Column('choice_id', Integer),
        Column('value', LargeBinary),
        Column('create_user_id', Integer, nullable=False),
        Column('create_date', DateTime, nullable=False, server_default=NOW),
        Column('modify_user_id', Integer, nullable=False),
        Column('modify_date', DateTime, nullable=False, server_default=NOW),
        Column('revision', Integer, nullable=False),
        ForeignKeyConstraint(['entity_id'],
                                [entity_table.c.id],
                                name='fk_%s_entity_id' % table_name,
                                ondelete='CASCADE'),
        ForeignKeyConstraint(['attribute_id'],
                                [attribute_table.c.id],
                                name='fk_%s_attribute_id' % table_name,
                                ondelete='CASCADE'),
        ForeignKeyConstraint(['choice_id'],
                                [choice_table.c.id],
                                name='fk_%s_choice_id' % table_name,
                                ondelete='CASCADE'),
        ForeignKeyConstraint(['create_user_id'],
                                [user_table.c.id],
                                name='fk_%s_create_user_id' % table_name,
                                ondelete='RESTRICT'),
        ForeignKeyConstraint(['modify_user_id'],
                                [user_table.c.id],
                                name='fk_%s_modify_user_id' % table_name,
                                ondelete='RESTRICT'),
        PrimaryKeyConstraint('id'),
        Index('ix_%s_create_user_id' % table_name, 'create_user_id'),
        Index('ix_%s_modify_user_id' % table_name, 'modify_user_id'),
        Index('ix_%s_entity_id' % table_name, 'entity_id'),
        Index('ix_%s_attribute_id' % table_name, 'attribute_id'),
        Index('ix_%s_choice_id' % table_name, 'choice_id'),
        CheckConstraint('create_date <= modify_date',
                        'ck_%s_valid_timeline' % table_name))
    return blob_table


def _build_blob_audit_table(metadata):
    table_audit_name = 'blob_audit'
    blob_audit_table = Table(table_name_audit, metadata,
        Column('id', Integer, nullable=False),
        Column('entity_id', Integer, nullable=False),
        Column('attribute_id', Integer, nullable=False),
        Column('choice_id', Integer),
        Column('value', LargeBinary),
        Column('create_user_id', Integer, nullable=False),
        Column('create_date', DateTime, nullable=False, server_default=NOW),
        Column('modify_user_id', Integer, nullable=False),
        Column('modify_date', DateTime, nullable=False, server_default=NOW),
        Column('revision', Integer, nullable=False),
        PrimaryKeyConstraint('id', 'revision'),
        Index('ix_%s_create_user_id' % table_name_audit, 'create_user_id'),
        Index('ix_%s_modify_user_id' % table_name_audit, 'modify_user_id'),
        CheckConstraint('create_date <= modify_date',
                        'ck_%s_valid_timeline' % table_name_audit))
    return blob_audit_table

