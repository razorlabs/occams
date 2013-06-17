"""
Adds customizable entity state workflow support
"""

from sqlalchemy import *
from migrate import *


NOW = text('CURRENT_TIMESTAMP')

BLAME_USER = u'bitcore@ucsd.edu'

STATE_NAME = 'state'
STATE_AUDIT_NAME = 'state_audit'

STATE_TABLE = Table(STATE_NAME, MetaData(),
    Column('id', Integer, primary_key=True),
    Column('name', String, nullable=False),
    Column('title', Unicode, nullable=False),
    Column('description', Unicode),
    Column('create_user_id', Integer, nullable=False),
    Column('create_date', DateTime, nullable=False, server_default=NOW),
    Column('modify_user_id', Integer, nullable=False),
    Column('modify_date', DateTime, nullable=False, server_default=NOW),
    Column('revision', Integer, nullable=False),
    ForeignKeyConstraint(['create_user_id'], ['user.id'],
                            name='fk_%s_create_user_id' % STATE_NAME,
                            ondelete='RESTRICT'),
    ForeignKeyConstraint(['modify_user_id'], ['user.id'],
                            name='fk_%s_modify_user_id' % STATE_NAME,
                            ondelete='RESTRICT'),
    PrimaryKeyConstraint('id'),
    UniqueConstraint('name', name='uq_%s_name' % STATE_NAME),
    Index('ix_%s_create_user_id' % STATE_NAME, 'create_user_id'),
    Index('ix_%s_modify_user_id' % STATE_NAME, 'modify_user_id'),
    CheckConstraint('create_date <= modify_date',
                    name='ck_%s_valid_timeline' % STATE_NAME))

STATE_AUDIT_TABLE = Table(STATE_AUDIT_NAME, MetaData(),
    Column('id', Integer, nullable=False),
    Column('name', String, nullable=False),
    Column('title', Unicode, nullable=False),
    Column('description', Unicode),
    Column('create_user_id', Integer, nullable=False),
    Column('create_date', DateTime, nullable=False, server_default=NOW),
    Column('modify_user_id', Integer, nullable=False),
    Column('modify_date', DateTime, nullable=False, server_default=NOW),
    Column('revision', Integer, nullable=False),
    PrimaryKeyConstraint('id', 'revision'),
    Index('ix_%s_create_user_id' % STATE_AUDIT_NAME, 'create_user_id'),
    Index('ix_%s_modify_user_id' % STATE_AUDIT_NAME, 'modify_user_id'),
    CheckConstraint('create_date <= modify_date',
                    name='ck_%s_valid_timeline' % STATE_AUDIT_NAME))


def upgrade(migrate_engine):
    metadata = MetaData(migrate_engine)
    entity_table = Table('entity', metadata, autoload=True)
    entity_audit_table = Table('entity_audit', metadata, autoload=True)
    user_table = Table('user', metadata, autoload=True)
    state_table = STATE_TABLE.tometadata(metadata)
    state_audit_table = STATE_AUDIT_TABLE.tometadata(metadata)

    # Create the new state tables
    state_table.create()
    state_audit_table.create()

    # Create new foreign key columns
    Column('state_id', Integer).create(entity_table, index_name='ix_entity_state_id')
    Column('state_id', Integer).create(entity_audit_table)

    ForeignKeyConstraint(
        [entity_table.c.state_id],
        [state_table.c.id],
        name='fk_entity_state_id'
        ).create()

    insert_query = state_table.insert().values(
        name=bindparam('name'),
        title=bindparam('title'),
        create_user_id=select([user_table.c.id], user_table.c.key == BLAME_USER).as_scalar(),
        modify_user_id=select([user_table.c.id], user_table.c.key == BLAME_USER).as_scalar(),
        revision=1)

    build_update = lambda t: t.update().values(
        state_id=select([state_table.c.id], state_table.c.name == cast(t.c.state, String)).as_scalar())

    with migrate_engine.begin() as connection:
        connection.execute(insert_query, [
            {'name': u'pending-entry', 'title': u'Pending Entry'},
            {'name': u'in-progress', 'title': u'In Progress'},
            {'name': u'pending-review', 'title': u'Pending Review'},
            {'name': u'pending-correction', 'title': u'Pending Correction'},
            {'name': u'complete', 'title': u'Complete'},
            # TODO: what to do with these:
            {'name': u'error', 'title': u'Error'},
            {'name': u'inaccurate', 'title': u'Inaccurate'}])
        connection.execute(build_update(entity_table))
        connection.execute(build_update(entity_audit_table))

    # Drop previous columns
    entity_table.c.state.drop()
    entity_audit_table.c.state.drop()


def downgrade(migrate_engine):
    raise Exception('Downgrading not supported')

