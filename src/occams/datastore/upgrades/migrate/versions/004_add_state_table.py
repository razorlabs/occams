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

    with migrate_engine.begin() as connection:
        (blame_id,) = connection.execute(
            select([user_table.c.id])
            .where(user_table.c.key == BLAME_USER)
            .limit(1)
            ).fetchone()

        # Create the new state tables
        state_table.create(bind=connection)
        state_audit_table.create(bind=connection)

        # Auto-populate with previous enums
        insert_query = (
            state_table
            .insert()
            .values(
                name=bindparam('name'),
                title=bindparam('title'),
                create_user_id=blame_id,
                modify_user_id=blame_id,
                revision=1))

        connection.execute(insert_query, [
            {'name': u'pending-entry', 'title': u'Pending Entry'},
            {'name': u'pending-review', 'title': u'Pending Review'},
            {'name': u'complete', 'title': u'Complete'},
            {'name': u'not-done', 'title': u'Not Done'},
            {'name': u'inline', 'title': u'Inline'},
            {'name': u'error', 'title': u'Error'},
            {'name': u'inaccurate', 'title': u'Inaccurate'},
            {'name': u'not-applicable', 'title': u'Not Applicable'},])

        # Create new foreign key columns
        state_id_column = Column('state_id', Integer)
        state_id_column.create(entity_table, index_name='ix_entity_state_id')
        fk = ForeignKeyConstraint(
            [state_id_column], [state_table.c.id], name='fk_entity_state_id')
        fk.create(connection)

        # Create audit columns
        state_id_audit_column = Column('state_id', Integer)
        state_id_audit_column.create(entity_audit_table, bind=connection)

        result = connection.execute(select([state_table]))
        state_id_map = dict([(r.name, r.id) for r in result])

        # Migrate the data
        for name, id in state_id_map.items():
            connection.execute(
                entity_table
                .update()
                .where(entity_table.c.state == name)
                .values(state_id=id))

        # Migrate the audit data
        for name, id in state_id_map.items():
            connection.execute(
                entity_audit_table
                .update()
                .where(entity_audit_table.c.state == name)
                .values(state_id=id))

        # Drop previous columns
        entity_table.c.state.drop(bind=connection)
        entity_audit_table.c.state.drop(bind=connection)


def downgrade(migrate_engine):
    metadata = MetaData(migrate_engine)
    entity_table = Table('entity', metadata, autoload=True)
    entity_audit_table = Table('entity_audit', metadata, autoload=True)
    user_table = Table('user', metadata, autoload=True)
    state_table = Table(STATE_NAME, metadata, autoload=True)
    state_audit_table = Table(STATE_AUDIT_NAME, metadata, autoload=True)

    with migrate_engine.begin() as connection:
        # build the states
        result = connection.execute(select([state_table]))
        states = dict([(r.id, r.name) for r in result])

        # Re-add the enum
        state_column = Column('state',
            Enum(*sorted(states.keys()), name='entity_state'),
            nullable=False,
            server_default='pending-entry')
        state_column.create(entity_table, bind=connection)

        # re-add the audit enum
        state_column = Column('state',
            Enum(*storted(states.keys()), name='entity_state'),
            nullable=False,
            server_default='pending-entry')
        state_column.create(entity_audit_table, bind=connection)

        # Migrate the data
        for id, name in states.items():
            connection.execute(
                entity_table
                .update()
                .where(entity_table.c.state_id == id)
                .values(state=name))

        # Migrate the audit data
        for id, name in state.items():
            connection.execute(
                entity_audit_table
                .update()
                .where(entity_audit_table.c.state_id == id)
                .values(state=name))

        # Drop the foreign key columns
        entity_table.c.state_id.drop(bind=connection)
        entity_audit_table.c.state_id.drop(bind=connection)

        # Drop previous columns
        state_table.drop(bind=connection)
        state_audit_table.drop(bind=connection)

