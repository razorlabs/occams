from sqlalchemy import *
from migrate import *

NOW = text('CURRENT_TIMESTAMP')

TEXT_NAME = 'text'
TEXT_AUDIT_NAME = 'text_audit'

TEXT_TABLE = Table(TEXT_NAME, MetaData(),
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
    ForeignKeyConstraint(['entity_id'], ['entity.id'],
                            name='fk_%s_entity_id' % TEXT_NAME,
                            ondelete='CASCADE'),
    ForeignKeyConstraint(['attribute_id'], ['attribute.id'],
                            name='fk_%s_attribute_id' % TEXT_NAME,
                            ondelete='CASCADE'),
    ForeignKeyConstraint(['choice_id'], ['choice.id'],
                            name='fk_%s_choice_id' % TEXT_NAME,
                            ondelete='CASCADE'),
    ForeignKeyConstraint(['create_user_id'], ['user.id'],
                            name='fk_%s_create_user_id' % TEXT_NAME,
                            ondelete='RESTRICT'),
    ForeignKeyConstraint(['modify_user_id'], ['user.id'],
                            name='fk_%s_modify_user_id' % TEXT_NAME,
                            ondelete='RESTRICT'),
    PrimaryKeyConstraint('id'),
    Index('ix_%s_create_user_id' % TEXT_NAME, 'create_user_id'),
    Index('ix_%s_modify_user_id' % TEXT_NAME, 'modify_user_id'),
    Index('ix_%s_entity_id' % TEXT_NAME, 'entity_id'),
    Index('ix_%s_attribute_id' % TEXT_NAME, 'attribute_id'),
    Index('ix_%s_choice_id' % TEXT_NAME, 'choice_id'),
    CheckConstraint('create_date <= modify_date',
                    name='ck_%s_valid_timeline' % TEXT_NAME))

TEXT_AUDIT_TABLE = Table(TEXT_AUDIT_NAME, MetaData(),
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
    Index('ix_%s_create_user_id' % TEXT_AUDIT_NAME, 'create_user_id'),
    Index('ix_%s_modify_user_id' % TEXT_AUDIT_NAME, 'modify_user_id'),
    CheckConstraint('create_date <= modify_date',
                    name='ck_%s_valid_timeline' % TEXT_AUDIT_NAME))


def upgrade(migrate_engine):
    u""" Creates a new text table and audit table and migrates the data """
    metadata = MetaData(migrate_engine)
    entity_table = Table('entity', metadata, autoload=True)
    attribute_table = Table('attribute', metadata, autoload=True)
    choice_table = Table('choice', metadata, autoload=True)
    string_table = Table('string', metadata, autoload=True)
    string_audit_table = Table('string_audit', metadata, autoload=True)
    user_table = Table('user', metadata, autoload=True)
    text_table = TEXT_TABLE.tometadata(metadata)
    text_audit_table = TEXT_AUDIT_TABLE.tometadata(metadata)

    # keep track of where we've moved the values to
    key_map = dict()

    with migrate_engine.begin() as connection:
        text_table.create(bind=connection)
        text_audit_table.create(bind=connection)

        text_query = (
            select([string_table])
            .select_from(
                string_table
                .join(attribute_table,
                      attribute_table.c.id == string_table.c.attribute_id))
            .where(attribute_table.c.type == 'text'))

        results = connection.execute(text_query)

        # move string values to their new text table home
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
            insert_result = connection.execute(insert_query)
            key_map[result.id] = insert_result.inserted_primary_key[0]

        ids = key_map.keys()

        text_audit_query = select([string_audit_table]).where(string_audit_table.c.id.in_(ids))
        results = connection.execute(text_audit_query)

        # move string audit values to their new text audit table home
        # NOTE there will be some data loss if string values have been
        # previously deleted
        for result in results:
            insert_query = text_audit_table.insert().values(
                id=key_map[result.id],
                entity_id=result.entity_id,
                attribute_id=result.attribute_id,
                value=result.value,
                create_user_id=result.create_user_id,
                create_date=result.create_date,
                modify_user_id=result.modify_user_id,
                modify_date=result.modify_date,
                revision=result.revision)
            connection.execute(insert_query)

        # remove the old locations
        connection.execute(string_table.delete().where(string_table.c.id.in_(ids)))
        connection.execute(string_audit_table.delete().where(string_audit_table.c.id.in_(ids)))

        # remove orphaned audit entries
        connection.execute(
            string_audit_table
            .delete()
            .where(string_audit_table.c.id.in_(
                select([string_audit_table.c.id])
                .select_from(
                    string_audit_table
                    .outerjoin(attribute_table,
                                attribute_table.c.id == string_audit_table.c.attribute_id))
                .where(attribute_table.c.type == 'text'))))



def downgrade(migrate_engine):
    u"""Migrates all text data back to the string table and deletes the text tables"""
    metadata = MetaData(migrate_engine)
    entity_table = Table('entity', metadata, autoload=True)
    attribute_table = Table('attribute', metadata, autoload=True)
    choice_table = Table('choice', metadata, autoload=True)
    string_table = Table('string', metadata, autoload=True)
    string_audit_table = Table('string_audit', metadata, autoload=True)
    user_table = Table('user', metadata, autoload=True)
    text_table = Table('text', metadata, autoload=True)
    text_audit_table = Table('text_audit', metadata, autoload=True)

    # keep track of where we've moved the values to
    key_map = dict()

    with migrate_engine.begin() as connection:
        results = connection.execute(select([text_table]))
        # move text values back to the string table
        for result in results:
            insert_query = string_table.insert().values(
                entity_id=result.entity_id,
                attribute_id=result.attribute_id,
                value=result.value,
                create_user_id=result.create_user_id,
                create_date=result.create_date,
                modify_user_id=result.modify_user_id,
                modify_date=result.modify_date,
                revision=result.revision)
            insert_result = connection.execute(insert_query)
            key_map[result.id] = insert_result.inserted_primary_key[0]

        ids = key_map.keys()

        text_audit_query = select([text_audit_table]) .where(text_audit_table.c.id.in_(ids))
        results = connection.execute(text_audit_query)

        # move text audit values back to the string audit table
        for result in results:
            insert_query = string_audit_table.insert().values(
                id=key_map[result.id],
                entity_id=result.entity_id,
                attribute_id=result.attribute_id,
                value=result.value,
                create_user_id=result.create_user_id,
                create_date=result.create_date,
                modify_user_id=result.modify_user_id,
                modify_date=result.modify_date,
                revision=result.revision)
            connection.execute(insert_query)

        # the text tables are no longer needed since their values have been moved
        text_audit_table.drop(bind=connection)
        text_table.drop(bind=connection)

