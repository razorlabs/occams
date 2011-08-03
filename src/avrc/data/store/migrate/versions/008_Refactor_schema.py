from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import *
from migrate import *


PY_NOW = datetime.now
SQL_NOW = text('CURRENT_TIMESTAMP')

SQL_FALSE = text('FALSE')


OldModel = declarative_base()


old_hierarchy_table = Table('hierarchy', OldModel.metadata,
    Column('parent_id', Integer, ForeignKey('specification.id', ondelete='CASCADE')),
    Column('child_id', Integer, ForeignKey('specification.id', ondelete='CASCADE')),
    PrimaryKeyConstraint('parent_id', 'child_id')
    )

class Specification(OldModel):
    __tablename__ = 'specification'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode, nullable=False, unique=True)
    documentation = Column(Unicode, nullable=False)
    title = Column(Unicode)
    description = Column(Text)
    is_tabable = Column(Boolean, nullable=False, default=False)
    is_association = Column(Boolean, nullable=False, default=False)
    is_virtual = Column(Boolean, nullable=False, default=False)
    is_eav = Column(Boolean, nullable=False, default=False)
    create_date = Column(DateTime, nullable=False, default=PY_NOW)
    modify_date = Column(DateTime, nullable=False, default=PY_NOW, onupdate=PY_NOW)


def upgrade(migrate_engine):
    """ Consolidates schema/specification into a single table.
    """
    metadata = MetaData(bind=migrate_engine)
    connection = metadata.bind.connect()

    schema_storage = Enum('table', 'eav', 'resource', name='schema_storage')
    
    new_schema_columns = (
        Column('base_schema_id', Integer, ForeignKey('schema.id', ondelete='CASCADE')),
        Column('name', String),
        Column('title', Unicode),
        Column('description', Unicode),
        Column('storage', schema_storage, nullable=False, server_default='eav'),
        Column('is_association', Boolean),
        Column('is_inline', Boolean),
        Column('create_date', DateTime, nullable=False, server_default=SQL_NOW),
        Column('create_user_id', Integer),
        Column('modify_date', DateTime, nullable=False, server_default=SQL_NOW, onupdate=PY_NOW),
        Column('modify_user_id', Integer),
        Column('remove_date', DateTime),
        Column('remove_user_id', Integer),
        )


    spec_table = Table('specification', metadata, autoload=True)
    hierarchy_table = Table('hierarchy', metadata, autoload=True)
    schema_table = Table('schema', metadata, autoload=True)

    schema_table.c.create_date.drop()
    schema_table.deregister()
    schema_table = Table('schema', metadata, autoload=True)

    schema_storage.create(metadata.bind)

    map((lambda c: c.create(schema_table)), new_schema_columns)

    Index('ix_schema_name', schema_table.c.name).create()
    Index('ix_base_schema_id', schema_table.c.base_schema_id).create()

    with connection.begin() as transaction:
        join_condition = (spec_table.c.id == hierarchy_table.c.child_id)
        join = spec_table.outerjoin(hierarchy_table, join_condition)
        query = select([spec_table, hierarchy_table.c.parent_id], from_obj=join)

        for result in connection.execute(query):
            connection.execute(
                schema_table.update() \
                .where(schema_table.c.specification_id == result.id) \
                .values(
                    base_schema_id=result.parent_id,
                    name=result.name,
                    title=result.title,
                    description=result.documentation,
                    create_date=result.create_date,
                    modify_date=result.modify_date,
                    )
                )
        transaction.commit()

    schema_table.c.specification_id.drop()
    schema_table.c.name.alter(nullable=False)
    schema_table.c.title.alter(nullable=False)

    hierarchy_table.drop()
    spec_table.drop()


def downgrade(migrate_engine):
    metadata = MetaData(bind=migrate_engine)
    connection = metadata.bind.connect()

    schema_storage = Enum('table', 'eav', 'resource', name='schema_storage')
    
    new_schema_columns = (
        Column('base_schema_id', Integer, ForeignKey('schema.id', ondelete='CASCADE')),
        Column('name', String),
        Column('title', Unicode),
        Column('description', Unicode),
        Column('storage', schema_storage, nullable=False, server_default='eav'),
        Column('is_association', Boolean),
        Column('is_inline', Boolean),
        Column('create_date', DateTime, nullable=False, server_default=SQL_NOW),
        Column('create_user_id', Integer),
        Column('modify_date', DateTime, nullable=False, server_default=SQL_NOW, onupdate=PY_NOW),
        Column('modify_user_id', Integer),
        Column('remove_date', DateTime),
        Column('remove_user_id', Integer),
        )


    spec_table = Specification.__table__.tometadata(metadata)
    hierarchy_table = old_hierarchy_table.tometadata(metadata)

    spec_table.create()
    hierarchy_table.create()
    schema_table = Table('schema', metadata, autoload=True)

    spec_column = Column('specification_id', Integer, ForeignKey('specification.id'))
    spec_column.create(table=schema_table, index_name='ix_schema_specification_id')

    with connection.begin() as transaction:
        query = select([schema_table]).order_by(schema_table.c.id.asc())

        for result in connection.execute(query):
            insert = connection.execute(
                spec_table.insert() \
                .values(
                    name=result.name,
                    documentation=result.description,
                    title=result.title,
                    is_eav=True,
                    create_date=result.create_date,
                    modify_date=result.modify_date,
                    )
                )

            (spec_id,) = insert.last_inserted_ids()

            connection.execute(
                schema_table.update() \
                .where(schema_table.c.id == result.id) \
                .values(specification_id=spec_id)
                )

        parent_table = schema_table.alias()
        join = (parent_table.c.id == schema_table.c.base_schema_id)
        query = select([parent_table.c.specification_id, schema_table.c.specification_id], join)

        # Rebuild the associations
        for (parent_id, child_id) in connection.execute(query):
            connection.execute(
                hierarchy_table.insert() \
                .values(
                    parent_id=parent_id,
                    child_id=child_id,
                    )
                )

        transaction.commit()

    schema_table.c.specification_id.alter(nullable=False)

    for column in schema_table.c:
        if column.name not in ('id', 'specification_id', 'create_date'):
            column.drop()

    schema_storage.drop(metadata.bind)
