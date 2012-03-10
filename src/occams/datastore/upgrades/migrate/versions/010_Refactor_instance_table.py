from datetime import datetime
from sqlalchemy import *
from migrate import *

PY_NOW = datetime.now
SQL_NOW = text('CURRENT_TIMESTAMP')


value_table_names = ('datetime', 'real', 'integer', 'object', 'string')


def upgrade(migrate_engine):
    """ Refactors the instance table.
        Un-reversable side effects: old instance titles are removed.
    """
    metadata = MetaData(migrate_engine)
    connection = metadata.bind.connect()

    new_columns = (
        Column('name', String),
        Column('title', Unicode),
        Column('description', Unicode),
        Column('state_id', Integer),
        Column('create_date', DateTime, nullable=False, server_default=SQL_NOW),
        Column('create_user_id', Integer),
        Column('modify_date', DateTime, nullable=False, server_default=SQL_NOW, onupdate=PY_NOW),
        Column('modify_user_id', Integer),
        Column('remove_date', DateTime),
        Column('remove_user_id', Integer),
        )

    entity_table = Table('instance', metadata, autoload=True)
    entity_table.rename('entity')
    entity_table.c.title.alter(name='old_title')
    entity_table.c.description.alter(name='old_description')
    entity_table.c.state_id.alter(name='old_state_id')
    entity_table.c.create_date.alter(name='old_create_date')
    entity_table.c.modify_date.alter(name='old_modify_date')

    entity_table.deregister()
    entity_table = Table('entity', metadata, autoload=True)
    schema_table = Table('schema', metadata, autoload=True)
    state_table = Table('state', metadata, autoload=True)

    DDL('ALTER SEQUENCE instance_id_seq RENAME TO entity_id_seq', on='postgresql').execute(metadata.bind)

    Index('instance_pkey', entity_table.c.id).rename('entity_pkey')
    Index('ix_instance_schema_id', entity_table.c.schema_id).rename('ix_entity_schema_id')

    # Rename foreign key
    fk = ForeignKeyConstraint(
        [entity_table.c.schema_id],
        [schema_table.c.id],
        name='instance_schema_id_fkey',
        )
    fk.drop()
    fk = ForeignKeyConstraint(
        [entity_table.c.schema_id],
        [schema_table.c.id],
        name='entity_schema_id_fkey',
        ondelete='CASCADE'
        )
    fk.create()

    create_column = lambda c: c.create(entity_table)
    map(create_column, new_columns)

    # Migrate data to new columns using new naming scheme
    with connection.begin() as transaction:
        join = (entity_table.c.schema_id == schema_table.c.id)
        schema_name_column = schema_table.c.name.label('schema_name')
        schema_title_column = schema_table.c.title.label('schema_title')
        query = select([entity_table, schema_name_column, schema_title_column], join)

        for result in connection.execute(query):
            if not result.is_active:
                remove_date = result.old_modify_date
            else:
                remove_date = None
                
            connection.execute(
                entity_table.update() \
                .where(entity_table.c.id == result.id)
                .values(
                    name=('%s-%d' % (result.schema_name, result.id)),
                    title=('%s - %d' % (result.schema_title, result.id)),
                    description=(result.old_description.strip() or None),
                    state_id=entity_table.c.old_state_id,
                    create_date=entity_table.c.old_create_date,
                    modify_date=entity_table.c.old_modify_date,
                    remove_date=remove_date,
                    )
                )
        transaction.commit()

        entity_table.c.old_title.drop()
        entity_table.c.old_description.drop()
        entity_table.c.old_state_id.drop()
        entity_table.c.is_active.drop()
        entity_table.c.old_create_date.drop()
        entity_table.c.old_modify_date.drop()

        entity_table.c.name.alter(nullable=False)
        entity_table.c.title.alter(nullable=False)

        fk = ForeignKeyConstraint(
            ['state_id'],
            ['state.id'],
            name='entity_state_id_fkey',
            ondelete='SET NULL',
            table=entity_table
            )

        fk.create()

        Index('ix_entity_name', entity_table.c.name).create()
        Index('ix_entity_state_id', entity_table.c.state_id).create()
        Index('ix_entity_remove_date', entity_table.c.remove_date).create()

        # Rename foreign keys
        for value_table_name in value_table_names:
            value_table = Table(value_table_name, metadata, autoload=True)
            fk = ForeignKeyConstraint(
                [value_table.c.instance_id],
                [entity_table.c.id],
                name='%s_instance_id_fkey' % value_table_name,
                )
            fk.drop()
            fk = ForeignKeyConstraint(
                [value_table.c.instance_id],
                [entity_table.c.id],
                name='%s_entity_id_fkey' % value_table_name,
                )
            fk.create()
            ix = Index('ix_%s_instance_id' % value_table_name, value_table.c.instance_id)
            ix.rename('ix_%s_entity_id' % value_table_name)

            value_table.c.instance_id.alter(name='entity_id')


def downgrade(migrate_engine):
    metadata = MetaData(migrate_engine)
    connection = metadata.bind.connect()

    new_columns = (
        Column('name', String),
        Column('title', Unicode),
        Column('description', Unicode),
        Column('state_id', Integer),
        Column('create_date', DateTime, nullable=False, server_default=SQL_NOW),
        Column('create_user_id', Integer),
        Column('modify_date', DateTime, nullable=False, server_default=SQL_NOW, onupdate=PY_NOW),
        Column('modify_user_id', Integer),
        Column('remove_date', DateTime),
        Column('remove_user_id', Integer),
        )


    instance_table = Table('entity', metadata, autoload=True)
    schema_table = Table('schema', metadata, autoload=True)
    state_table = Table('state', metadata, autoload=True)

    instance_table.rename('instance')

    Column('is_active', Boolean, default=True).create(instance_table)

    DDL('ALTER SEQUENCE entity_id_seq RENAME TO instance_id_seq', on='postgresql').execute(metadata.bind)

    Index('entity_pkey', instance_table.c.id).rename('instance_pkey')
    Index('ix_entity_schema_id', instance_table.c.schema_id).rename('ix_instance_schema_id')
    Index('ix_entity_state_id', instance_table.c.state_id).drop()

    fk = ForeignKeyConstraint(
        [instance_table.c.schema_id],
        [schema_table.c.id],
        name='entity_schema_id_fkey',
        )
    fk.drop()
    fk = ForeignKeyConstraint(
        [instance_table.c.schema_id],
        [schema_table.c.id],
        name='instance_schema_id_fkey',
        ondelete='CASCADE'
        )
    fk.create()

    UniqueConstraint(instance_table.c.title, name='instance_title_key').create()

    with connection.begin() as transaction:
        for result in connection.execute(select([instance_table])):
            connection.execute(
                instance_table.update() \
                .where(instance_table.c.id == result.id)
                .values(
                    description=u'',
                    is_active=(result.remove_date is None)
                    )
                )
        transaction.commit()

        instance_table.c.name.drop()
        instance_table.c.is_active.alter(nullable=False)
        instance_table.c.description.alter(nullable=False)
        instance_table.c.state_id.alter(nullable=False)
        instance_table.c.create_user_id.drop()
        instance_table.c.modify_user_id.drop()
        instance_table.c.remove_user_id.drop()
        instance_table.c.remove_date.drop()

        fk = ForeignKeyConstraint(
            ['state_id'],
            ['state.id'],
            name='entity_state_id_fkey',
            table=instance_table
            )

        fk.drop()

        fk = ForeignKeyConstraint(
            ['state_id'],
            ['state.id'],
            name='instance_state_id_fkey',
            ondelete='CASCADE',
            table=instance_table
            )

        fk.create()

        for value_table_name in value_table_names:
            value_table = Table(value_table_name, metadata, autoload=True)
            fk = ForeignKeyConstraint(
                [value_table.c.entity_id],
                [instance_table.c.id],
                name='%s_entity_id_fkey' % value_table_name,
                )
            fk.drop()
            fk = ForeignKeyConstraint(
                [value_table.c.entity_id],
                [instance_table.c.id],
                name='%s_instance_id_fkey' % value_table_name,
                )
            fk.create()
            ix = Index('ix_%s_entity_id' % value_table_name, value_table.c.entity_id)
            ix.rename('ix_%s_instance_id' % value_table_name)

            value_table.c.entity_id.alter(name='instance_id')
