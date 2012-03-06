from sqlalchemy import *
from migrate import *

NOW = text('CURRENT_TIMESTAMP')

TIMELINE_CHECK_SQL = 'create_date <= modify_date AND modify_date <= remove_date'
TIMELINE_NAME_FMT = '%s_valid_edit_timeline'

def upgrade(migrate_engine):
    """ Upgrades the entity table with a new collect data metadata property
    """
    constraint_name = TIMELINE_NAME_FMT % 'entity'
    metadata = MetaData(migrate_engine)
    connection = metadata.bind.connect()
    entity_table = Table('entity', metadata, autoload=True)
    columns = (
        Column('collect_date', Date),
        Column('create_date', DateTime),
        Column('create_user_id', Integer),
        Column('modify_date', DateTime,),
        Column('modify_user_id', Integer),
        Column('remove_date', DateTime),
        Column('remove_user_id', Integer),
        )

    # Drop the old constrains so they don't interfere
    CheckConstraint(TIMELINE_CHECK_SQL, name=constraint_name, table=entity_table).drop()
    Index('ix_entity_remove_date', entity_table.c.remove_date).drop()

    # Rename old columns as we're going to rearrange them
    entity_table.c.create_date.alter(name='old_create_date')
    entity_table.c.create_user_id.alter(name='old_create_user_id')
    entity_table.c.modify_date.alter(name='old_modify_date')
    entity_table.c.modify_user_id.alter(name='old_modify_user_id')
    entity_table.c.remove_date.alter(name='old_remove_date')
    entity_table.c.remove_user_id.alter(name='old_remove_user_id')

    # Add the new columns
    for column in columns:
        column.create(entity_table)

    metadata.clear()
    entity_table = Table('entity', metadata, autoload=True)

    # Add the new constraints
    CheckConstraint(TIMELINE_CHECK_SQL, name=constraint_name, table=entity_table).create()
    Index('ix_entity_remove_date', entity_table.c.remove_date).create()

    with connection.begin() as transaction:
        # Copy the old data into the new columns
        connection.execute(
            entity_table.update()
            .values(
                collect_date=entity_table.c.old_create_date,
                create_date=entity_table.c.old_create_date,
                create_user_id=entity_table.c.old_create_user_id,
                modify_date=entity_table.c.old_modify_date,
                modify_user_id=entity_table.c.old_modify_user_id,
                remove_date=entity_table.c.old_remove_date,
                remove_user_id=entity_table.c.old_remove_user_id,
                )
            )

        transaction.commit()

    # Remove the old columns
    entity_table.c.old_create_date.drop()
    entity_table.c.old_create_user_id.drop()
    entity_table.c.old_modify_date.drop()
    entity_table.c.old_modify_user_id.drop()
    entity_table.c.old_remove_date.drop()
    entity_table.c.old_remove_user_id.drop()

    entity_table.c.collect_date.alter(nullable=False)
    entity_table.c.create_date.alter(nullable=False, server_default=NOW)
    entity_table.c.modify_date.alter(nullable=False, server_default=NOW)


def downgrade(migrate_engine):
    metadata = MetaData(migrate_engine)
    entity_table = Table('entity', metadata, autoload=True)
    entity_table.c.collect_date.drop()
