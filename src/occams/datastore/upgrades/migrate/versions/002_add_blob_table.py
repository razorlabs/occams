from sqlalchemy import *
from migrate import *

NOW = text('CURRENT_TIMESTAMP')

BLOB_NAME = 'blob'
BLOB_AUDIT_NAME = 'blob_audit'

BLOB_TABLE = Table(BLOB_NAME, MetaData(),
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
    ForeignKeyConstraint(['entity_id'],['entity.id'],
                            name='fk_%s_entity_id' % BLOB_NAME,
                            ondelete='CASCADE'),
    ForeignKeyConstraint(['attribute_id'], ['attribute.id'],
                            name='fk_%s_attribute_id' % BLOB_NAME,
                            ondelete='CASCADE'),
    ForeignKeyConstraint(['choice_id'], ['choice.id'],
                            name='fk_%s_choice_id' % BLOB_NAME,
                            ondelete='CASCADE'),
    ForeignKeyConstraint(['create_user_id'], ['user.id'],
                            name='fk_%s_create_user_id' % BLOB_NAME,
                            ondelete='RESTRICT'),
    ForeignKeyConstraint(['modify_user_id'], ['user.id'],
                            name='fk_%s_modify_user_id' % BLOB_NAME,
                            ondelete='RESTRICT'),
    PrimaryKeyConstraint('id'),
    Index('ix_%s_create_user_id' % BLOB_NAME, 'create_user_id'),
    Index('ix_%s_modify_user_id' % BLOB_NAME, 'modify_user_id'),
    Index('ix_%s_entity_id' % BLOB_NAME, 'entity_id'),
    Index('ix_%s_attribute_id' % BLOB_NAME, 'attribute_id'),
    Index('ix_%s_choice_id' % BLOB_NAME, 'choice_id'),
    CheckConstraint('create_date <= modify_date',
                    name='ck_%s_valid_timeline' % BLOB_NAME))

BLOB_AUDIT_TABLE = Table(BLOB_AUDIT_NAME, MetaData(),
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
    Index('ix_%s_create_user_id' % BLOB_AUDIT_NAME, 'create_user_id'),
    Index('ix_%s_modify_user_id' % BLOB_AUDIT_NAME, 'modify_user_id'),
    CheckConstraint('create_date <= modify_date',
                    name='ck_%s_valid_timeline' % BLOB_AUDIT_NAME))


def upgrade(migrate_engine):
    u""" Creates blob tables """
    metadata = MetaData(migrate_engine)
    entity_table = Table('entity', metadata, autoload=True)
    attribute_table = Table('attribute', metadata, autoload=True)
    choice_table = Table('choice', metadata, autoload=True)
    string_table = Table('string', metadata, autoload=True)
    string_audit_table = Table('string_audit', metadata, autoload=True)
    user_table = Table('user', metadata, autoload=True)
    blob_table = BLOB_TABLE.tometadata(metadata)
    blob_audit_table = BLOB_AUDIT_TABLE.tometadata(metadata)

    with migrate_engine.begin() as connection:
        blob_table.create(bind=connection)
        blob_audit_table.create(bind=connection)


def downgrade(migrate_engine):
    u"""Drops blob tables"""
    metadata = MetaData(migrate_engine)
    entity_table = Table('entity', metadata, autoload=True)
    attribute_table = Table('attribute', metadata, autoload=True)
    choice_table = Table('choice', metadata, autoload=True)
    string_table = Table('string', metadata, autoload=True)
    string_audit_table = Table('string_audit', metadata, autoload=True)
    user_table = Table('user', metadata, autoload=True)
    blob_table = Table(BLOB_NAME, metadata, autoload=True)
    blob_audit_table = Table(BLOB_AUDIT_NAME, metadata, autoload=True)

    with migrate_engine.begin() as connection:
        blob_audit_table.drop(bind=connection)
        blob_table.drop(bind=connection)

