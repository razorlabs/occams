from sqlalchemy import *
from migrate import *

CASCADE = 'CASCADE'
RESTRICT = 'RESTRICT'
SET_NULL = 'SET NULL'


def fk(*args, **kw):
    fk = ForeignKeyConstraint(*args, **kw)
    fk.drop()
    fk.create()


def upgrade(migrate_engine):
    metadata = MetaData(bind=migrate_engine, reflect=True)
    tables = metadata.tables

    ## "aliquot"
    fk(['specimen_id'], ['specimen.id'], name='aliquot_specimen_id_fkey', table=tables['aliquot'], ondelete=CASCADE)
    fk(['analysis_status_id'], ['specimen_aliquot_term.id'], name='aliquot_analysis_status_id_fkey', table=tables['aliquot'], ondelete=CASCADE)
    fk(['special_instruction_id'], ['specimen_aliquot_term.id'], name='aliquot_special_instruction_id_fkey', table=tables['aliquot'], ondelete=CASCADE)
    fk(['state_id'], ['specimen_aliquot_term.id'], name='aliquot_state_id_fkey', table=tables['aliquot'], ondelete=CASCADE)
    fk(['storage_site_id'], ['specimen_aliquot_term.id'], name='aliquot_storage_site_id_fkey', table=tables['aliquot'], ondelete=CASCADE)
    fk(['type_id'], ['specimen_aliquot_term.id'], name='aliquot_type_id_fkey', table=tables['aliquot'], ondelete=CASCADE)

    ## "aliquot_history"
    fk(['aliquot_id'], ['aliquot.id'], name='aliquot_history_aliquot_id_fkey', table=tables['aliquot_history'], ondelete=CASCADE)
    fk(['state_id'], ['specimen_aliquot_term.id'], name='aliquot_history_state_id_fkey', table=tables['aliquot_history'], ondelete=CASCADE)

    ## "attribute"
    fk(['field_id'], ['field.id'], name='attribute_field_id_fkey', table=tables['attribute'], ondelete=CASCADE)
    fk(['schema_id'], ['schema.id'], name='attribute_schema_id_fkey', table=tables['attribute'], ondelete=CASCADE)

    ## "datetime"
    fk(['attribute_id'], ['attribute.id'], name='datetime_attribute_id_fkey', table=tables['datetime'], ondelete=CASCADE)
    fk(['instance_id'], ['instance.id'], name='datetime_instance_id_fkey', table=tables['datetime'], ondelete=CASCADE)

    ## "domain"
    # No references

    ## "domain_schema"
    fk(['domain_id'], ['domain.id'], name='domain_schema_domain_id_fkey', table=tables['domain_schema'], ondelete=CASCADE)
    fk(['schema_id'], ['schema.id'], name='domain_schema_schema_id_fkey', table=tables['domain_schema'], ondelete=CASCADE)

    ## "drug"
    fk(['drug_category_id'], ['drug_category.id'], name='drug_drug_category_id_fkey', table=tables['drug'], ondelete=CASCADE)
    fk(['drug_status_id'], ['drug_status.id'], name='drug_drug_status_id_fkey', table=tables['drug'], ondelete=CASCADE)

    ## "drug_category"
    # No references

    ## "drug_name"
    fk(['drug_id'], ['drug.id'], name='drug_name_drug_id_fkey', table=tables['drug_name'], ondelete=CASCADE)

    ## "drug_status"
    # No references

    ## "enrollment"
    fk(['domain_id'], ['domain.id'], name='enrollment_domain_id_fkey', table=tables['enrollment'], ondelete=CASCADE)
    fk(['subject_id'], ['subject.id'], name='enrollment_subject_id_fkey', table=tables['enrollment'], ondelete=CASCADE)

    ## "enrollment_instance"
    fk(['enrollment_id'], ['enrollment.id'], name='enrollment_instance_enrollment_id_fkey', table=tables['enrollment_instance'], ondelete=RESTRICT)
    fk(['instance_id'], ['instance.id'], name='enrollment_instance_instance_id_fkey', table=tables['enrollment_instance'], ondelete=CASCADE)

    ## "field"
    fk(['schema_id'], ['schema.id'], name='field_schema_id_fkey', table=tables['field'], ondelete=SET_NULL)
    fk(['type_id'], ['type.id'], name='field_type_id_fkey', table=tables['field'], ondelete=CASCADE)
    fk(['vocabulary_id'], ['vocabulary.id'], name='field_vocabulary_id_fkey', table=tables['field'], ondelete=SET_NULL)

    ## "fieldset"
    # No references

    ## "fieldset_fieldsetitem"
    fk(['fieldset_id'], ['fieldset.id'], name='fieldset_fieldsetitem_fieldset_id_fkey', table=tables['fieldset_fieldsetitem'], ondelete=CASCADE)
    fk(['item_id'], ['fieldsetitem.id'], name='fieldset_fieldsetitem_item_id_fkey', table=tables['fieldset_fieldsetitem'], ondelete=CASCADE)

    ## "fieldsetitem"
    # No references

    ## "hierarchy"
    fk(['child_id'], ['specification.id'], name='hierarchy_child_id_fkey', table=tables['hierarchy'], ondelete=CASCADE)
    fk(['parent_id'], ['specification.id'], name='hierarchy_parent_id_fkey', table=tables['hierarchy'], ondelete=CASCADE)

    ## "include"
    fk(['include_id'], ['specification.id'], name='include_include_id_fkey', table=tables['include'], ondelete=CASCADE)
    fk(['main_id'], ['specification.id'], name='include_main_id_fkey', table=tables['include'], ondelete=CASCADE)

    ## "instance"
    fk(['schema_id'], ['schema.id'], name='instance_schema_id_fkey', table=tables['instance'], ondelete=CASCADE)
    fk(['state_id'], ['state.id'], name='instance_state_id_fkey', table=tables['instance'], ondelete=CASCADE)

    ## "integer"
    fk(['instance_id'], ['instance.id'], name='integer_instance_id_fkey', table=tables['integer'], ondelete=CASCADE)
    fk(['attribute_id'], ['attribute.id'], name='integer_attribute_id_fkey', table=tables['integer'], ondelete=CASCADE)

    ## "invariant"
    fk(['schema_id'], ['schema.id'], name='invariant_schema_id_fkey', table=tables['invariant'], ondelete=CASCADE)

    ## "keyword"
    fk(['instance_id'], ['instance.id'], name='keyword_instance_id_fkey', table=tables['keyword'], ondelete=CASCADE)

    ## "medication"
    fk(['drug_id'], ['drug.id'], name='medication_drug_id_fkey', table=tables['medication'], ondelete=CASCADE)
    fk(['subject_id'], ['subject.id'], name='medication_subject_id_fkey', table=tables['medication'], ondelete=CASCADE)
    fk(['visit_id'], ['visit.id'], name='medication_visit_id_fkey', table=tables['medication'], ondelete=SET_NULL)

    ## "object"
    fk(['attribute_id'], ['attribute.id'], name='object_attribute_id_fkey', table=tables['object'], ondelete=CASCADE)
    fk(['instance_id'], ['instance.id'], name='object_instance_id_fkey', table=tables['object'], ondelete=CASCADE)
    fk(['value'], ['instance.id'], name='object_instance_id_fkey', table=tables['object'], ondelete=CASCADE)

    ## "partner"
    fk(['subject_id'], ['subject.id'], name='partner_subject_id_fkey', table=tables['partner'], ondelete=CASCADE)
    fk(['enrolled_subject_id'], ['subject.id'], name='partner_subject_id_fkey', table=tables['partner'], ondelete=SET_NULL)

    ## "partner_instance"
    fk(['partner_id'], ['partner.id'], name='partner_instance_partner_id_fkey', table=tables['partner_instance'], ondelete=RESTRICT)
    fk(['instance_id'], ['instance.id'], name='partner_instance_instance_id_fkey', table=tables['partner_instance'], ondelete=CASCADE)

    ## "protocol"
    fk(['domain_id'], ['domain.id'], name='protocol_domain_id_fkey', table=tables['protocol'], ondelete=CASCADE)

    ## "protocol_schema"
    fk(['protocol_id'], ['protocol.id'], name='protocol_schema_protocol_id_fkey', table=tables['protocol_schema'], ondelete=CASCADE)
    fk(['schema_id'], ['schema.id'], name='protocol_schema_schema_id_fkey', table=tables['protocol_schema'], ondelete=CASCADE)

    ## "range"
    fk(['attribute_id'], ['attribute.id'], name='range_attribute_id_fkey', table=tables['range'], ondelete=CASCADE)
    fk(['instance_id'], ['instance.id'], name='range_instance_id_fkey', table=tables['range'], ondelete=CASCADE)

    ## "real"
    fk(['attribute_id'], ['attribute.id'], name='real_attribute_id_fkey', table=tables['real'], ondelete=CASCADE)
    fk(['instance_id'], ['instance.id'], name='real_instance_id_fkey', table=tables['real'], ondelete=CASCADE)

    ## "schema"
    fk(['specification_id'], ['specification.id'], name='schema_specification_id_fkey', table=tables['schema'], ondelete=CASCADE)

    ## "schema_fieldset"
    fk(['fieldset_id'], ['fieldset.id'], name='schema_fieldset_fieldset_id_fkey', table=tables['schema_fieldset'], ondelete=CASCADE)
    fk(['schema_id'], ['schema.id'], name='schema_fieldset_schema_id_fkey', table=tables['schema_fieldset'], ondelete=CASCADE)

    ## "selection"
    fk(['attribute_id'], ['attribute.id'], name='selection_attribute_id_fkey', table=tables['selection'], ondelete=CASCADE)
    fk(['instance_id'], ['instance.id'], name='selection_instance_id_fkey', table=tables['selection'], ondelete=CASCADE)
    fk(['value'], ['term.id'], name='selection_value_fkey', table=tables['selection'], ondelete=CASCADE)

    ## "specification"
    # No references

    ## "specimen"
    fk(['protocol_id'], ['protocol.id'], name='specimen_protocol_id_fkey', table=tables['specimen'], ondelete=CASCADE)
    fk(['destination_id'], ['specimen_aliquot_term.id'], name='specimen_destination_id_fkey', table=tables['specimen'], ondelete=CASCADE)
    fk(['state_id'], ['specimen_aliquot_term.id'], name='specimen_state_id_fkey', table=tables['specimen'], ondelete=CASCADE)
    # The mispelling is intentional, it's actually mispelled in the model too
    fk(['tupe_type_id'], ['specimen_aliquot_term.id'], name='specimen_tupe_type_id_fkey', table=tables['specimen'], ondelete=CASCADE)
    fk(['type_id'], ['specimen_aliquot_term.id'], name='specimen_type_id_fkey', table=tables['specimen'], ondelete=CASCADE)
    fk(['subject_id'], ['subject.id'], name='specimen_subject_id_fkey', table=tables['specimen'], ondelete=CASCADE)

    ## "specimen_aliquot_term"
    # No references

    # "state"
    # No references

    ## "string"
    fk(['attribute_id'], ['attribute.id'], name='string_attribute_id_fkey', table=tables['string'], ondelete=CASCADE)
    fk(['instance_id'], ['instance.id'], name='string_instance_id_fkey', table=tables['string'], ondelete=CASCADE)

    ## "subject"
    # No references

    ## "subject_instance"
    fk(['subject_id'], ['subject.id'], name='subject_instance_subject_id_fkey', table=tables['subject_instance'], ondelete=RESTRICT)
    fk(['instance_id'], ['instance.id'], name='subject_instance_instance_id_fkey', table=tables['subject_instance'], ondelete=CASCADE)

    ## "symptom"
    fk(['subject_id'], ['subject.id'], name='symptom_subject_id_fkey', table=tables['symptom'], ondelete=CASCADE)
    fk(['symptom_type_id'], ['symptom_type.id'], name='symptom_symptom_type_id_fkey', table=tables['symptom'], ondelete=CASCADE)

    ## "symptom_type"
    # No references

    ## "term"
    # No references

    ## "type"
    # No references

    ## "visit"
    fk(['subject_id'], ['subject.id'], name='visit_subject_id_fkey', table=tables['visit'], ondelete=CASCADE)

    ## "visit_instance"
    fk(['instance_id'], ['instance.id'], name='visit_instance_instance_id_fkey', table=tables['visit_instance'], ondelete=RESTRICT)
    fk(['visit_id'], ['visit.id'], name='visit_instance_visit_id_fkey', table=tables['visit_instance'], ondelete=CASCADE)

    ## "visit_protocol"
    fk(['protocol_id'], ['protocol.id'], name='visit_protocol_protocol_id_fkey', table=tables['visit_protocol'], ondelete=CASCADE)
    fk(['visit_id'], ['visit.id'], name='visit_protocol_visit_id_fkey', table=tables['visit_protocol'], ondelete=CASCADE)

    ## "vocabulary"
    # No references

    ## "vocabulary_term"
    fk(['term_id'], ['term.id'], name='vocabulary_term_term_id_fkey', table=tables['vocabulary_term'], ondelete=CASCADE)
    fk(['vocabulary_id'], ['vocabulary.id'], name='vocabulary_term_vocabulary_id_fkey', table=tables['vocabulary_term'], ondelete=CASCADE)


def downgrade(migrate_engine):
    metadata = MetaData(bind=migrate_engine, reflect=True)
    tables = metadata.tables

    ## "aliquot"
    fk(['specimen_id'], ['specimen.id'], name='aliquot_specimen_id_fkey', table=tables['aliquot'],)
    fk(['analysis_status_id'], ['specimen_aliquot_term.id'], name='aliquot_analysis_status_id_fkey', table=tables['aliquot'],)
    fk(['special_instruction_id'], ['specimen_aliquot_term.id'], name='aliquot_special_instruction_id_fkey', table=tables['aliquot'],)
    fk(['state_id'], ['specimen_aliquot_term.id'], name='aliquot_state_id_fkey', table=tables['aliquot'],)
    fk(['storage_site_id'], ['specimen_aliquot_term.id'], name='aliquot_storage_site_id_fkey', table=tables['aliquot'],)
    fk(['type_id'], ['specimen_aliquot_term.id'], name='aliquot_type_id_fkey', table=tables['aliquot'],)

    ## "aliquot_history"
    fk(['aliquot_id'], ['aliquot.id'], name='aliquot_history_aliquot_id_fkey', table=tables['aliquot_history'],)
    fk(['state_id'], ['specimen_aliquot_term.id'], name='aliquot_history_state_id_fkey', table=tables['aliquot_history'],)

    ## "attribute"
    fk(['field_id'], ['field.id'], name='attribute_field_id_fkey', table=tables['attribute'],)
    fk(['schema_id'], ['schema.id'], name='attribute_schema_id_fkey', table=tables['attribute'],)

    ## "datetime"
    fk(['attribute_id'], ['attribute.id'], name='datetime_attribute_id_fkey', table=tables['datetime'],)
    fk(['instance_id'], ['instance.id'], name='datetime_instance_id_fkey', table=tables['datetime'],)

    ## "domain"
    # No references

    ## "domain_schema"
    fk(['domain_id'], ['domain.id'], name='domain_schema_domain_id_fkey', table=tables['domain_schema'],)
    fk(['schema_id'], ['schema.id'], name='domain_schema_schema_id_fkey', table=tables['domain_schema'],)

    ## "drug"
    fk(['drug_category_id'], ['drug_category.id'], name='drug_drug_category_id_fkey', table=tables['drug'],)
    fk(['drug_status_id'], ['drug_status.id'], name='drug_drug_status_id_fkey', table=tables['drug'],)

    ## "drug_category"
    # No references

    ## "drug_name"
    fk(['drug_id'], ['drug.id'], name='drug_name_drug_id_fkey', table=tables['drug_name'],)

    ## "drug_status"
    # No references

    ## "enrollment"
    fk(['domain_id'], ['domain.id'], name='enrollment_domain_id_fkey', table=tables['enrollment'],)
    fk(['subject_id'], ['subject.id'], name='enrollment_subject_id_fkey', table=tables['enrollment'],)

    ## "enrollment_instance"
    fk(['enrollment_id'], ['enrollment.id'], name='enrollment_instance_enrollment_id_fkey', table=tables['enrollment_instance'],)
    fk(['instance_id'], ['instance.id'], name='enrollment_instance_instance_id_fkey', table=tables['enrollment_instance'],)

    ## "field"
    fk(['schema_id'], ['schema.id'], name='field_schema_id_fkey', table=tables['field'],)
    fk(['type_id'], ['type.id'], name='field_type_id_fkey', table=tables['field'],)
    fk(['vocabulary_id'], ['vocabulary.id'], name='field_vocabulary_id_fkey', table=tables['field'],)

    ## "fieldset"
    # No references

    ## "fieldset_fieldsetitem"
    fk(['fieldset_id'], ['fieldset.id'], name='fieldset_fieldsetitem_fieldset_id_fkey', table=tables['fieldset_fieldsetitem'],)
    fk(['item_id'], ['fieldsetitem.id'], name='fieldset_fieldsetitem_item_id_fkey', table=tables['fieldset_fieldsetitem'],)

    ## "fieldsetitem"
    # No references

    ## "hierarchy"
    fk(['child_id'], ['specification.id'], name='hierarchy_child_id_fkey', table=tables['hierarchy'],)
    fk(['parent_id'], ['specification.id'], name='hierarchy_parent_id_fkey', table=tables['hierarchy'],)

    ## "include"
    fk(['include_id'], ['specification.id'], name='include_include_id_fkey', table=tables['include'],)
    fk(['main_id'], ['specification.id'], name='include_main_id_fkey', table=tables['include'],)

    ## "instance"
    fk(['schema_id'], ['schema.id'], name='instance_schema_id_fkey', table=tables['instance'],)
    fk(['state_id'], ['state.id'], name='instance_state_id_fkey', table=tables['instance'],)

    ## "integer"
    fk(['instance_id'], ['instance.id'], name='integer_instance_id_fkey', table=tables['integer'],)
    fk(['attribute_id'], ['attribute.id'], name='integer_attribute_id_fkey', table=tables['integer'],)

    ## "invariant"
    fk(['schema_id'], ['schema.id'], name='invariant_schema_id_fkey', table=tables['invariant'],)

    ## "keyword"
    fk(['instance_id'], ['instance.id'], name='keyword_instance_id_fkey', table=tables['keyword'],)

    ## "medication"
    fk(['drug_id'], ['drug.id'], name='medication_drug_id_fkey', table=tables['medication'],)
    fk(['subject_id'], ['subject.id'], name='medication_subject_id_fkey', table=tables['medication'],)
    fk(['visit_id'], ['visit.id'], name='medication_visit_id_fkey', table=tables['medication'],)

    ## "object"
    fk(['attribute_id'], ['attribute.id'], name='object_attribute_id_fkey', table=tables['object'],)
    fk(['instance_id'], ['instance.id'], name='object_instance_id_fkey', table=tables['object'],)
    fk(['value'], ['instance.id'], name='object_instance_id_fkey', table=tables['object'],)

    ## "partner"
    fk(['subject_id'], ['subject.id'], name='partner_subject_id_fkey', table=tables['partner'],)
    fk(['enrolled_subject_id'], ['subject.id'], name='partner_subject_id_fkey', table=tables['partner'],)

    ## "partner_instance"
    fk(['partner_id'], ['partner.id'], name='partner_instance_partner_id_fkey', table=tables['partner_instance'],)
    fk(['instance_id'], ['instance.id'], name='partner_instance_instance_id_fkey', table=tables['partner_instance'],)

    ## "protocol"
    fk(['domain_id'], ['domain.id'], name='protocol_domain_id_fkey', table=tables['protocol'],)

    ## "protocol_schema"
    fk(['protocol_id'], ['protocol.id'], name='protocol_schema_protocol_id_fkey', table=tables['protocol_schema'],)
    fk(['schema_id'], ['schema.id'], name='protocol_schema_schema_id_fkey', table=tables['protocol_schema'],)

    ## "range"
    fk(['attribute_id'], ['attribute.id'], name='range_attribute_id_fkey', table=tables['range'],)
    fk(['instance_id'], ['instance.id'], name='range_instance_id_fkey', table=tables['range'],)

    ## "real"
    fk(['attribute_id'], ['attribute.id'], name='real_attribute_id_fkey', table=tables['real'],)
    fk(['instance_id'], ['instance.id'], name='real_instance_id_fkey', table=tables['real'],)

    ## "schema"
    fk(['specification_id'], ['specification.id'], name='schema_specification_id_fkey', table=tables['schema'],)

    ## "schema_fieldset"
    fk(['fieldset_id'], ['fieldset.id'], name='schema_fieldset_fieldset_id_fkey', table=tables['schema_fieldset'],)
    fk(['schema_id'], ['schema.id'], name='schema_fieldset_schema_id_fkey', table=tables['schema_fieldset'],)

    ## "selection"
    fk(['attribute_id'], ['attribute.id'], name='selection_attribute_id_fkey', table=tables['selection'],)
    fk(['instance_id'], ['instance.id'], name='selection_instance_id_fkey', table=tables['selection'],)
    fk(['value'], ['term.id'], name='selection_value_fkey', table=tables['selection'],)

    ## "specification"
    # No references

    ## "specimen"
    fk(['protocol_id'], ['protocol.id'], name='specimen_protocol_id_fkey', table=tables['specimen'],)
    fk(['destination_id'], ['specimen_aliquot_term.id'], name='specimen_destination_id_fkey', table=tables['specimen'],)
    fk(['state_id'], ['specimen_aliquot_term.id'], name='specimen_state_id_fkey', table=tables['specimen'],)
    # The mispelling is intentional, it's actually mispelled in the model too
    fk(['tupe_type_id'], ['specimen_aliquot_term.id'], name='specimen_tupe_type_id_fkey', table=tables['specimen'],)
    fk(['type_id'], ['specimen_aliquot_term.id'], name='specimen_type_id_fkey', table=tables['specimen'],)
    fk(['subject_id'], ['subject.id'], name='specimen_subject_id_fkey', table=tables['specimen'],)

    ## "specimen_aliquot_term"
    # No references

    # "state"
    # No references

    ## "string"
    fk(['attribute_id'], ['attribute.id'], name='string_attribute_id_fkey', table=tables['string'],)
    fk(['instance_id'], ['instance.id'], name='string_instance_id_fkey', table=tables['string'],)

    ## "subject"
    # No references

    ## "subject_instance"
    fk(['subject_id'], ['subject.id'], name='subject_instance_subject_id_fkey', table=tables['subject_instance'],)
    fk(['instance_id'], ['instance.id'], name='subject_instance_instance_id_fkey', table=tables['subject_instance'],)

    ## "symptom"
    fk(['subject_id'], ['subject.id'], name='symptom_subject_id_fkey', table=tables['symptom'],)
    fk(['symptom_type_id'], ['symptom_type.id'], name='symptom_symptom_type_id_fkey', table=tables['symptom'],)

    ## "symptom_type"
    # No references

    ## "term"
    # No references

    ## "type"
    # No references

    ## "visit"
    fk(['subject_id'], ['subject.id'], name='visit_subject_id_fkey', table=tables['visit'],)

    ## "visit_instance"
    fk(['instance_id'], ['instance.id'], name='visit_instance_instance_id_fkey', table=tables['visit_instance'],)
    fk(['visit_id'], ['visit.id'], name='visit_instance_visit_id_fkey', table=tables['visit_instance'],)

    ## "visit_protocol"
    fk(['protocol_id'], ['protocol.id'], name='visit_protocol_protocol_id_fkey', table=tables['visit_protocol'],)
    fk(['visit_id'], ['visit.id'], name='visit_protocol_visit_id_fkey', table=tables['visit_protocol'],)

    ## "vocabulary"
    # No references

    ## "vocabulary_term"
    fk(['term_id'], ['term.id'], name='vocabulary_term_term_id_fkey', table=tables['vocabulary_term'],)
    fk(['vocabulary_id'], ['vocabulary.id'], name='vocabulary_term_vocabulary_id_fkey', table=tables['vocabulary_term'],)

