from sqlalchemy import *
from migrate import *

NOW = text('CURRENT_TIMESTAMP')

def upgrade(migrate_engine):
    u""" Creates a new text table and audit table and migrates the data """
    metadata = MetaData(migrate_engine)

    entity_table = Table('entity', metadata, autoload=True)
    attribute_table = Table('attribute', metadata, autoload=True)
    choice_table = Table('choice', metadata, autoload=True)
    string_table = Table('string', metadata, autoload=True)
    string_audit_table = Table('string_audit', metdata, audoload=True)
    user_table = Table('user', metadata, autoload=True)

    text_table = _build_text_table(metadata)
    text_audit_table = _build_text_audit_table(metadata)

    # keep track of where we've moved the values to
    primary_key_map = dict()

    with migrate_engine.begin() as connection:
        text_query = select([string_table]).select_from(
            string_table
            .join(attribute_table,
                  attribute_table.c.id == string_table.c.attribute_id)
            .where(attribute_table.c.type == 'text'))

        with connection.execute(text_query) as results:
            for result in results:
                insert_query = text_table.insert().values(
                    entity_id=result.entity_id,
                    attribute_id=result.attribute_id,
                    value=result.value,
                    create_user_id=result.create_user_id,
                    create_date=result.create_date,
                    modify_user_id=result.modify_user_id,
                    modify_date=result.modify_date,
                    revision=result.revision)
                insert_result = connection.execute(text_table)
                primary_key_map[result.id] = insert_result.inserted_primary_key

        text_audit_query = (
            select([string_audit_table])
            .where(string_audit_table.c.id.in_(primary_key_map.keys())))

        with connection.execute(text_audit_query) as results:
            for result in results:
                insert_query = text_audit_table.insert().values(
                    id=primary_key_map[result.id],
                    entity_id=result.entity_id,
                    attribute_id=result.attribute_id,
                    value=result.value,
                    create_user_id=result.create_user_id,
                    create_date=result.create_date,
                    modify_user_id=result.modify_user_id,
                    modify_date=result.modify_date,
                    revision=result.revision)
                connection.execute(insert_query)

        connection.execute(
            string_table
            .delete()
            .where(string_table.c.id.in_(primary_key_map.keys())))

        connection.execute(
            string_audit_table
            .delete()
            .where(string_audit_table.c.id.in_(primary_key_map.keys())))


def downgrade(migrate_engine):
    u"""Migrates all text data back to the string table and deletes the text tables"""

    metadata = MetaData(migrate_engine)

    entity_table = Table('entity', metadata, autoload=True)
    attribute_table = Table('attribute', metadata, autoload=True)
    choice_table = Table('choice', metadata, autoload=True)
    string_table = Table('string', metadata, autoload=True)
    string_audit_table = Table('string_audit', metdata, audoload=True)
    user_table = Table('user', metadata, autoload=True)
    text_table = Table('text', metadata, autoload=True)
    text_audit_table = Table('text_audit', metadata, autoload=True)

    # keep track of where we've moved the values to
    primary_key_map = dict()

    with migrate_engine.begin() as connection:
        text_query = select([text_table])

        with connection.execute(text_query) as results:
            for result in results:
                insert_query = text_table.insert().values(
                    entity_id=result.entity_id,
                    attribute_id=result.attribute_id,
                    value=result.value,
                    create_user_id=result.create_user_id,
                    create_date=result.create_date,
                    modify_user_id=result.modify_user_id,
                    modify_date=result.modify_date,
                    revision=result.revision)
                insert_result = connection.execute(text_table)
                primary_key_map[result.id] = insert_result.inserted_primary_key

        text_audit_query = (
            select([text_audit_table])
            .where(text_audit_table.c.id.in_(primary_key_map.keys())))

        with connection.execute(text_audit_query) as results:
            for result in results:
                insert_query = text_audit_table.insert().values(
                    id=primary_key_map[result.id],
                    entity_id=result.entity_id,
                    attribute_id=result.attribute_id,
                    value=result.value,
                    create_user_id=result.create_user_id,
                    create_date=result.create_date,
                    modify_user_id=result.modify_user_id,
                    modify_date=result.modify_date,
                    revision=result.revision)
                connection.execute(insert_query)

    text_audit_table.drop()
    text_table.drop()


def _build_text_table(metadata):
    table_name = 'text'
    text_table = Table(table_name, metadata,
        Column('id', Integer, primary_key=True),
        Column('entity_id', Integer, nullable=False),
        Column('attribute_id', Integer, nullable=False),
        Column('choice_id', Integer),
        Column('value', UnicodeText),
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
    return text_table


def _build_text_audit_table(metadata):
    table_audit_name = 'text_audit'
    text_audit_table = Table(table_name_audit, metadata,
        Column('id', Integer),
        Column('entity_id', Integer, nullable=False),
        Column('attribute_id', Integer, nullable=False),
        Column('choice_id', Integer),
        Column('value', UnicodeText),
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
    return text_audit_table

