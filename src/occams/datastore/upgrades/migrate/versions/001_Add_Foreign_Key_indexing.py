from sqlalchemy import *
from migrate import *

# Indexes to rename (using sqalachemy style naming)
to_rename = (
    'specimen_subject_id',
    'specimen_protocol_id',
    'specimen_state_id',
    'specimen_type_id',
    'specimen_destination_id',
    'specimen_tube_type_id',
    'aliquot_specimen_id',
    'aliquot_type_id',
    'aliquot_state_id',
    'aliquot_storage_site_id',
    'aliquot_analysis_status_id',
    'aliquot_special_instruction_id',
    )

# New indexes for table columns (one per fk)
new_indices = (
   ('protocol', 'domain_id'),
   ('enrollment', 'domain_id'),
   ('enrollment', 'subject_id'),
   ('aliquot_history', 'aliquot_id'),
   ('aliquot_history', 'state_id'),
   ('schema', 'specification_id'),
   ('invariant', 'schema_id'),
   ('field', 'type_id'),
   ('field', 'schema_id'),
   ('field', 'vocabulary_id'),
   ('attribute', 'schema_id'),
   ('attribute', 'field_id'),
   ('instance', 'schema_id'),
   ('keyword', 'instance_id'),
   ('datetime', 'instance_id'),
   ('integer', 'instance_id'),
   ('range', 'instance_id'),
   ('real', 'instance_id'),
   ('selection', 'instance_id'),
   ('object', 'instance_id'),
   ('string', 'instance_id'),
)

def upgrade(migrate_engine):
    metadata = MetaData(bind=migrate_engine, reflect=True)
    tables = metadata.tables

    # Fix model error on selection composed index.
    wrong = [tables['real'].c.attribute_id, tables['real'].c.value,]
    right = [tables['selection'].c.attribute_id, tables['selection'].c.value,]
    Index('selection_attribute_value', *wrong).drop(migrate_engine)
    Index('selection_attribute_value', *right).create(migrate_engine)

    # Fix index names
    for table_name, column_name in new_indices:
        index_name = '_'.join(['ix', table_name, column_name])
        column = getattr(tables[table_name].c, column_name)
        Index(index_name, column).create(migrate_engine)

    targets = list(tables['specimen'].indexes) + list(tables['aliquot'].indexes)

    # Add new indexes
    for index in targets:
        if index.name in to_rename:
            index.rename('ix_' + index.name)


def downgrade(migrate_engine):
    metadata = MetaData(bind=migrate_engine, reflect=True)
    tables = metadata.tables

    # Unifix selection error
    wrong = [tables['real'].c.attribute_id, tables['real'].c.value,]
    right = [tables['selection'].c.attribute_id, tables['selection'].c.value,]
    Index('selection_attribute_value', *right).drop(migrate_engine)
    Index('selection_attribute_value', *wrong).create(migrate_engine)

    # Unfix index names
    for table_name, column_name in new_indices:
        index_name = '_'.join(['ix', table_name, column_name])
        column = getattr(tables[table_name].c, column_name)
        Index(index_name, column).drop(migrate_engine)

    targets = list(tables['specimen'].indexes) + list(tables['aliquot'].indexes)

    # Remove new indexes
    for index in targets:
        old_name = index.name[len('ix_'):]
        if old_name in to_rename:
            index.rename(old_name)

