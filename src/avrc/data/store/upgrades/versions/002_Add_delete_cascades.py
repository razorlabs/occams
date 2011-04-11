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
    fk([tables['aliquot'].c.specimen_id], [tables['specimen'].c.id], ondelete=CASCADE)
    fk([tables['aliquot'].c.analysis_status_id], [tables['specimen_aliquot_term'].c.id], ondelete=CASCADE)
    fk([tables['aliquot'].c.special_instruction_id], [tables['specimen_aliquot_term'].c.id], ondelete=CASCADE)
    fk([tables['aliquot'].c.state_id], [tables['specimen_aliquot_term'].c.id], ondelete=CASCADE)
    fk([tables['aliquot'].c.storage_site_id], [tables['specimen_aliquot_term'].c.id], ondelete=CASCADE)
    fk([tables['aliquot'].c.type_id], [tables['specimen_aliquot_term'].c.id], ondelete=CASCADE)

    ## "aliquot_history"
    fk([tables['aliquot_history'].c.aliquot_id], [tables['aliquot'].c.id], ondelete=CASCADE)
    fk([tables['aliquot_history'].c.state_id], [tables['specimen_aliquot_term'].c.id], ondelete=CASCADE)

    ## "attribute"
    fk([tables['attribute'].c.field_id], [tables['field'].c.id], ondelete=CASCADE)
    fk([tables['attribute'].c.schema_id], [tables['schema'].c.id], ondelete=CASCADE)

    ## "datetime"
    fk([tables['datetime'].c.attribute_id], [tables['attribute'].c.id], ondelete=CASCADE)
    fk([tables['datetime'].c.instance_id], [tables['instance'].c.id], ondelete=CASCADE)

    ## "domain"
    # No references

    ## "domain_schema"
    fk([tables['domain_schema'].c.domain_id], [tables['domain'].c.id], ondelete=CASCADE)
    fk([tables['domain_schema'].c.schema_id], [tables['schema'].c.id], ondelete=CASCADE)

    ## "drug"
    fk([tables['drug'].c.drug_category_id], [tables['drug_category'].c.id], ondelete=CASCADE)
    fk([tables['drug'].c.drug_status_id], [tables['drug_status'].c.id], ondelete=CASCADE)

    ## "drug_category"
    # No references

    ## "drug_name"
    fk([tables['drug_name'].c.drug_id], [tables['drug'].c.id], ondelete=CASCADE)

    ## "drug_status"
    # No references

    ## "enrollment"
    fk([tables['enrollment'].c.domain_id], [tables['domain'].c.id], ondelete=CASCADE)
    fk([tables['enrollment'].c.subject_id], [tables['subject'].c.id], ondelete=CASCADE)

    ## "enrollment_instance"
    fk([tables['enrollment_instance'].c.enrollment_id], [tables['enrollment'].c.id], ondelete=RESTRICT)
    fk([tables['enrollment_instance'].c.instance_id], [tables['instance'].c.id], ondelete=CASCADE)

    ## "field"
    fk([tables['field'].c.schema_id], [tables['schema'].c.id], ondelete=SET_NULL)
    fk([tables['field'].c.type_id], [tables['type'].c.id], ondelete=CASCADE)
    fk([tables['field'].c.vocabulary_id], [tables['vocabulary'].c.id], ondelete=SET_NULL)

    ## "fieldset"
    # No references

    ## "fieldset_fieldsetitem"
    fk([tables['fieldset_fieldsetitem'].c.fieldset_id], [tables['fieldset'].c.id], ondelete=CASCADE)
    fk([tables['fieldset_fieldsetitem'].c.item_id], [tables['fieldsetitem'].c.id], ondelete=CASCADE)

    ## "fieldsetitem"
    # No references

    ## "hierarchy"
    fk([tables['hierarchy'].c.child_id], [tables['specification'].c.id], ondelete=CASCADE)
    fk([tables['hierarchy'].c.parent_id], [tables['specification'].c.id], ondelete=CASCADE)

    ## "include"
    fk([tables['include'].c.include_id], [tables['specification'].c.id], ondelete=CASCADE)
    fk([tables['include'].c.main_id], [tables['specification'].c.id], ondelete=CASCADE)

    ## "instance"
    fk([tables['instance'].c.schema_id], [tables['schema'].c.id], ondelete=CASCADE)
    fk([tables['instance'].c.state_id], [tables['state'].c.id], ondelete=CASCADE)

    ## "integer"
    fk([tables['integer'].c.instance_id], [tables['instance'].c.id], ondelete=CASCADE)
    fk([tables['integer'].c.attribute_id], [tables['attribute'].c.id], ondelete=CASCADE)

    ## "invariant"
    fk([tables['invariant'].c.schema_id], [tables['schema'].c.id], ondelete=CASCADE)

    ## "keyword"
    fk([tables['keyword'].c.instance_id], [tables['instance'].c.id], ondelete=CASCADE)

    ## "medication"
    fk([tables['medication'].c.drug_id], [tables['drug'].c.id], ondelete=CASCADE)
    fk([tables['medication'].c.subject_id], [tables['subject'].c.id], ondelete=CASCADE)
    fk([tables['medication'].c.visit_id], [tables['visit'].c.id], ondelete=SET_NULL)

    ## "object"
    fk([tables['object'].c.attribute_id], [tables['attribute'].c.id], ondelete=CASCADE)
    fk([tables['object'].c.instance_id], [tables['instance'].c.id], ondelete=CASCADE)
    fk([tables['object'].c.value], [tables['instance'].c.id], ondelete=CASCADE)

    ## "partner"
    fk([tables['partner'].c.subject_id], [tables['subject'].c.id], ondelete=CASCADE)
    fk([tables['partner'].c.enrolled_subject_id], [tables['subject'].c.id], ondelete=SET_NULL)

    ## "partner_instance"
    fk([tables['partner_instance'].c.partner_id], [tables['partner'].c.id], ondelete=RESTRICT)
    fk([tables['partner_instance'].c.instance_id], [tables['instance'].c.id], ondelete=CASCADE)

    ## "protocol"
    fk([tables['protocol'].c.domain_id], [tables['domain'].c.id], ondelete=CASCADE)

    ## "protocol_schema"
    fk([tables['protocol_schema'].c.protocol_id], [tables['protocol'].c.id], ondelete=CASCADE)
    fk([tables['protocol_schema'].c.schema_id], [tables['schema'].c.id], ondelete=CASCADE)

    ## "range"
    fk([tables['range'].c.attribute_id], [tables['attribute'].c.id], ondelete=CASCADE)
    fk([tables['range'].c.instance_id], [tables['instance'].c.id], ondelete=CASCADE)

    ## "real"
    fk([tables['real'].c.attribute_id], [tables['attribute'].c.id], ondelete=CASCADE)
    fk([tables['real'].c.instance_id], [tables['instance'].c.id], ondelete=CASCADE)

    ## "schema"
    fk([tables['schema'].c.specification_id], [tables['specification'].c.id], ondelete=CASCADE)

    ## "schema_fieldset"
    fk([tables['schema_fieldset'].c.fieldset_id], [tables['fieldset'].c.id], ondelete=CASCADE)
    fk([tables['schema_fieldset'].c.schema_id], [tables['schema'].c.id], ondelete=CASCADE)

    ## "selection"
    fk([tables['selection'].c.attribute_id], [tables['attribute'].c.id], ondelete=CASCADE)
    fk([tables['selection'].c.instance_id], [tables['instance'].c.id], ondelete=CASCADE)
    fk([tables['selection'].c.value], [tables['term'].c.id], ondelete=CASCADE)

    ## "specification"
    # No references

    ## "specimen"
    fk([tables['specimen'].c.protocol_id], [tables['protocol'].c.id], ondelete=CASCADE)
    fk([tables['specimen'].c.destination_id], [tables['specimen_aliquot_term'].c.id], ondelete=CASCADE)
    fk([tables['specimen'].c.state_id], [tables['specimen_aliquot_term'].c.id], ondelete=CASCADE)
    # The mispelling is intentional, it's actually mispelled in the model too
    fk([tables['specimen'].c.tupe_type_id], [tables['specimen_aliquot_term'].c.id], ondelete=CASCADE)
    fk([tables['specimen'].c.type_id], [tables['specimen_aliquot_term'].c.id], ondelete=CASCADE)
    fk([tables['specimen'].c.subject_id], [tables['subject'].c.id], ondelete=CASCADE)

    ## "specimen_aliquot_term"
    # No references

    # "state"
    # No references

    ## "string"
    fk([tables['string'].c.attribute_id], [tables['attribute'].c.id], ondelete=CASCADE)
    fk([tables['string'].c.instance_id], [tables['instance'].c.id], ondelete=CASCADE)

    ## "subject"
    # No references

    ## "subject_instance"
    fk([tables['subject_instance'].c.subject_id], [tables['subject'].c.id], ondelete=RESTRICT)
    fk([tables['subject_instance'].c.instance_id], [tables['instance'].c.id], ondelete=CASCADE)

    ## "symptom"
    fk([tables['symptom'].c.subject_id], [tables['subject'].c.id], ondelete=CASCADE)
    fk([tables['symptom'].c.symptom_type_id], [tables['symptom_type'].c.id], ondelete=CASCADE)

    ## "symptom_type"
    # No references

    ## "term"
    # No references

    ## "type"
    # No references

    ## "visit"
    fk([tables['visit'].c.subject_id], [tables['subject'].c.id], ondelete=CASCADE)

    ## "visit_instance"
    fk([tables['visit_instance'].c.instance_id], [tables['instance'].c.id], ondelete=RESTRICT)
    fk([tables['visit_instance'].c.visit_id], [tables['visit'].c.id], ondelete=CASCADE)

    ## "visit_protocol"
    fk([tables['visit_protocol'].c.protocol_id], [tables['protocol'].c.id], ondelete=CASCADE)
    fk([tables['visit_protocol'].c.visit_id], [tables['visit'].c.id], ondelete=CASCADE)

    ## "vocabulary"
    # No references

    ## "vocabulary_term"
    fk([tables['vocabulary_term'].c.term_id], [tables['term'].c.id], ondelete=CASCADE)
    fk([tables['vocabulary_term'].c.vocabulary_id], [tables['vocabulary'].c.id], ondelete=CASCADE)


def downgrade(migrate_engine):
    metadata = MetaData(bind=migrate_engine, reflect=True)
    tables = metadata.tables

    ## "aliquot"
    fk([tables['aliquot'].c.specimen_id], [tables['specimen'].c.id],)
    fk([tables['aliquot'].c.analysis_status_id], [tables['specimen_aliquot_term'].c.id],)
    fk([tables['aliquot'].c.special_instruction_id], [tables['specimen_aliquot_term'].c.id],)
    fk([tables['aliquot'].c.state_id], [tables['specimen_aliquot_term'].c.id],)
    fk([tables['aliquot'].c.storage_site_id], [tables['specimen_aliquot_term'].c.id],)
    fk([tables['aliquot'].c.type_id], [tables['specimen_aliquot_term'].c.id],)

    ## "aliquot_history"
    fk([tables['aliquot_history'].c.aliquot_id], [tables['aliquot'].c.id],)
    fk([tables['aliquot_history'].c.state_id], [tables['specimen_aliquot_term'].c.id],)

    ## "attribute"
    fk([tables['attribute'].c.field_id], [tables['field'].c.id],)
    fk([tables['attribute'].c.schema_id], [tables['schema'].c.id],)

    ## "datetime"
    fk([tables['datetime'].c.attribute_id], [tables['attribute'].c.id],)
    fk([tables['datetime'].c.instance_id], [tables['instance'].c.id],)

    ## "domain"
    # No references

    ## "domain_schema"
    fk([tables['domain_schema'].c.domain_id], [tables['domain'].c.id],)
    fk([tables['domain_schema'].c.schema_id], [tables['schema'].c.id],)

    ## "drug"
    fk([tables['drug'].c.drug_category_id], [tables['drug_category'].c.id],)
    fk([tables['drug'].c.drug_status_id], [tables['drug_status'].c.id],)

    ## "drug_category"
    # No references

    ## "drug_name"
    fk([tables['drug_name'].c.drug_id], [tables['drug'].c.id],)

    ## "drug_status"
    # No references

    ## "enrollment"
    fk([tables['enrollment'].c.domain_id], [tables['domain'].c.id],)
    fk([tables['enrollment'].c.subject_id], [tables['subject'].c.id],)

    ## "enrollment_instance"
    fk([tables['enrollment_instance'].c.enrollment_id], [tables['enrollment'].c.id],)
    fk([tables['enrollment_instance'].c.instance_id], [tables['instance'].c.id],)

    ## "field"
    fk([tables['field'].c.schema_id], [tables['schema'].c.id],)
    fk([tables['field'].c.type_id], [tables['type'].c.id],)
    fk([tables['field'].c.vocabulary_id], [tables['vocabulary'].c.id],)

    ## "fieldset"
    # No references

    ## "fieldset_fieldsetitem"
    fk([tables['fieldset_fieldsetitem'].c.fieldset_id], [tables['fieldset'].c.id],)
    fk([tables['fieldset_fieldsetitem'].c.item_id], [tables['fieldsetitem'].c.id],)

    ## "fieldsetitem"
    # No references

    ## "hierarchy"
    fk([tables['hierarchy'].c.child_id], [tables['specification'].c.id],)
    fk([tables['hierarchy'].c.parent_id], [tables['specification'].c.id],)

    ## "include"
    fk([tables['include'].c.include_id], [tables['specification'].c.id],)
    fk([tables['include'].c.main_id], [tables['specification'].c.id],)

    ## "instance"
    fk([tables['instance'].c.schema_id], [tables['schema'].c.id],)
    fk([tables['instance'].c.state_id], [tables['state'].c.id],)

    ## "integer"
    fk([tables['integer'].c.instance_id], [tables['instance'].c.id],)
    fk([tables['integer'].c.attribute_id], [tables['attribute'].c.id],)

    ## "invariant"
    fk([tables['invariant'].c.schema_id], [tables['schema'].c.id],)

    ## "keyword"
    fk([tables['keyword'].c.instance_id], [tables['instance'].c.id],)

    ## "medication"
    fk([tables['medication'].c.drug_id], [tables['drug'].c.id],)
    fk([tables['medication'].c.subject_id], [tables['subject'].c.id],)
    fk([tables['medication'].c.visit_id], [tables['visit'].c.id],)

    ## "object"
    fk([tables['object'].c.attribute_id], [tables['attribute'].c.id],)
    fk([tables['object'].c.instance_id], [tables['instance'].c.id],)
    fk([tables['object'].c.value], [tables['instance'].c.id],)

    ## "partner"
    fk([tables['partner'].c.subject_id], [tables['subject'].c.id],)
    fk([tables['partner'].c.enrolled_subject_id], [tables['subject'].c.id],)

    ## "partner_instance"
    fk([tables['partner_instance'].c.partner_id], [tables['partner'].c.id],)
    fk([tables['partner_instance'].c.instance_id], [tables['instance'].c.id],)

    ## "protocol"
    fk([tables['protocol'].c.domain_id], [tables['domain'].c.id],)

    ## "protocol_schema"
    fk([tables['protocol_schema'].c.protocol_id], [tables['protocol'].c.id],)
    fk([tables['protocol_schema'].c.schema_id], [tables['schema'].c.id],)

    ## "range"
    fk([tables['range'].c.attribute_id], [tables['attribute'].c.id],)
    fk([tables['range'].c.instance_id], [tables['instance'].c.id],)

    ## "real"
    fk([tables['real'].c.attribute_id], [tables['attribute'].c.id],)
    fk([tables['real'].c.instance_id], [tables['instance'].c.id],)

    ## "schema"
    fk([tables['schema'].c.specification_id], [tables['specification'].c.id],)

    ## "schema_fieldset"
    fk([tables['schema_fieldset'].c.fieldset_id], [tables['fieldset'].c.id],)
    fk([tables['schema_fieldset'].c.schema_id], [tables['schema'].c.id],)

    ## "selection"
    fk([tables['selection'].c.attribute_id], [tables['attribute'].c.id],)
    fk([tables['selection'].c.instance_id], [tables['instance'].c.id],)
    fk([tables['selection'].c.value], [tables['term'].c.id],)

    ## "specification"
    # No references

    ## "specimen"
    fk([tables['specimen'].c.protocol_id], [tables['protocol'].c.id],)
    fk([tables['specimen'].c.destination_id], [tables['specimen_aliquot_term'].c.id],)
    fk([tables['specimen'].c.state_id], [tables['specimen_aliquot_term'].c.id],)
    # The mispelling is intentional, it's actually mispelled in the model too
    fk([tables['specimen'].c.tupe_type_id], [tables['specimen_aliquot_term'].c.id],)
    fk([tables['specimen'].c.type_id], [tables['specimen_aliquot_term'].c.id],)
    fk([tables['specimen'].c.subject_id], [tables['subject'].c.id],)

    ## "specimen_aliquot_term"
    # No references

    # "state"
    # No references

    ## "string"
    fk([tables['string'].c.attribute_id], [tables['attribute'].c.id],)
    fk([tables['string'].c.instance_id], [tables['instance'].c.id],)

    ## "subject"
    # No references

    ## "subject_instance"
    fk([tables['subject_instance'].c.instance_id], [tables['instance'].c.id],)
    fk([tables['subject_instance'].c.subject_id], [tables['subject'].c.id],)

    ## "symptom"
    fk([tables['symptom'].c.subject_id], [tables['subject'].c.id],)
    fk([tables['symptom'].c.symptom_type_id], [tables['symptom_type'].c.id],)

    ## "symptom_type"
    # No references

    ## "term"
    # No references

    ## "type"
    # No references

    ## "visit"
    fk([tables['visit'].c.subject_id], [tables['subject'].c.id],)

    ## "visit_instance"
    fk([tables['visit_instance'].c.instance_id], [tables['instance'].c.id],)
    fk([tables['visit_instance'].c.visit_id], [tables['visit'].c.id],)

    ## "visit_protocol"
    fk([tables['visit_protocol'].c.protocol_id], [tables['protocol'].c.id],)
    fk([tables['visit_protocol'].c.visit_id], [tables['visit'].c.id],)

    ## "vocabulary"
    # No references

    ## "vocabulary_term"
    fk([tables['vocabulary_term'].c.term_id], [tables['term'].c.id],)
    fk([tables['vocabulary_term'].c.vocabulary_id], [tables['vocabulary'].c.id],)
