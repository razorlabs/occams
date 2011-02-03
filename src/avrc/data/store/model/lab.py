""" Lab Models
"""

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import orm

from avrc.data.store.model import Model


class SpecimenAliquotTerm(Model):
    """
    . . .
    """
    __tablename__ = 'specimen_aliquot_term'

    id = sa.Column(sa.Integer, primary_key=True)

    vocabulary_name = sa.Column(sa.Unicode, nullable=False, index=True)

    title = sa.Column(sa.Unicode)

    token = sa.Column(sa.Unicode, nullable=False)

    value = sa.Column(sa.Unicode, nullable=False)

    is_active = sa.Column(sa.Boolean, nullable=False, default=True, index=True)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)

    __table_args = (
        sa.UniqueConstraint('vocabulary_name', 'token', 'value'),
        {})


class Specimen(Model):
    """ Speccialized table for specimen data. Note that only one specimen can be
        drawn from a patient/protocol/type.

        Attributes:
            id: (int) machine generated primary key
            subject_id: (int) reference to the subject this specimen was
                drawn from
            subject: (object) the relation to the subject
            protocol_id: (int) reference to the protocol this specimen was
                drawn for
            protocol: (object) the relation to the protocol
            state: (str) current state of the specimen
            collect_date: (datetime) the date/time said specimen was collected
            type: (str) the type of specimen
            destination: (str) the destination of where the specimen is sent to.
            tubes: (int) number of tubes collected (optional, if applicable)
            volume_per_tube: (int) volume of each tube (optional, if applicable)
            notes: (str) optinal notes that can be entered by users (optional)
            aliquot: (list) convenience relation to the aliquot parts generated
                from this speciemen
            is_active: (bool) internal marker to indicate this entry is
                being used.
            create_date: (datetime) internal metadata of when entry was created
            modify_date: (datetime) internal metadata of when entry was modified
    """
    __tablename__ = 'specimen'

    id = sa.Column(sa.Integer, primary_key=True)

    subject_id = sa.Column(sa.ForeignKey('subject.id'), nullable=False)

    subject = orm.relation('Subject', uselist=False)

    protocol_id = sa.Column(sa.ForeignKey('protocol.id'), nullable=False)

    protocol = orm.relation('Protocol', uselist=False)

    state_id = sa.Column(sa.ForeignKey('specimen_aliquot_term.id'), nullable=False)

    state = orm.relation('SpecimenAliquotTerm', uselist=False, primaryjoin=state_id == SpecimenAliquotTerm.id)

    collect_date = sa.Column(sa.Date)

    collect_time = sa.Column(sa.Time)

    type_id = sa.Column(sa.ForeignKey('specimen_aliquot_term.id'), nullable=False)

    type = orm.relation('SpecimenAliquotTerm', uselist=False, primaryjoin=type_id == SpecimenAliquotTerm.id)

    destination_id = sa.Column(sa.ForeignKey('specimen_aliquot_term.id'), nullable=False)

    destination = orm.relation('SpecimenAliquotTerm', uselist=False, primaryjoin=destination_id == SpecimenAliquotTerm.id)

    tubes = sa.Column(sa.Integer)

    tupe_type_id = sa.Column(sa.ForeignKey('specimen_aliquot_term.id'), nullable=False)

    tube_type = orm.relation('SpecimenAliquotTerm', uselist=False, primaryjoin=tupe_type_id == SpecimenAliquotTerm.id)

    notes = sa.Column(sa.Unicode)

    aliquot = orm.relation('Aliquot')

    is_active = sa.Column(sa.Boolean, nullable=False, default=True, index=True)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)

    __table_args = (
        sa.UniqueConstraint('subject_id', 'protocol_id', 'type'),
        {})


sa.Index('specimen_subject_id', Specimen.subject_id)
sa.Index('specimen_protocol_id', Specimen.protocol_id)
sa.Index('specimen_state_id', Specimen.state_id)
sa.Index('specimen_type_id', Specimen.type_id)
sa.Index('specimen_destination_id', Specimen.destination_id)
sa.Index('specimen_tube_type_id', Specimen.tupe_type_id)


class AliquotHistory(Model):
    """ Keeps track of aliquot state history. """
    __tablename__ = 'aliquot_history'

    id = sa.Column(sa.Integer, primary_key=True)

    aliquot_id = sa.Column(sa.ForeignKey('aliquot.id'), nullable=False)

    state_id = sa.Column(sa.ForeignKey('specimen_aliquot_term.id'), nullable=False)

    state = orm.relation('SpecimenAliquotTerm', uselist=False, primaryjoin=state_id == SpecimenAliquotTerm.id)

    action_date = sa.Column(sa.DateTime, nullable=False)

    to = sa.Column(sa.Unicode, nullable=False)


class Aliquot(Model):
    """ Specialized table for aliquot parts generated from a specimen.

        Attributes:
            id: (int) machine generated primary key
            specimen_id: (int) the specimen this aliquot was generated from
    """
    __tablename__ = 'aliquot'

    id = sa.Column(sa.Integer, primary_key=True)

    specimen_id = sa.Column(sa.ForeignKey('specimen.id'), nullable=False)

    specimen = orm.relation('Specimen', uselist=False)

    type_id = sa.Column(sa.ForeignKey('specimen_aliquot_term.id'), nullable=False)

    type = orm.relation('SpecimenAliquotTerm', uselist=False, primaryjoin=type_id == SpecimenAliquotTerm.id)

    volume = sa.Column(sa.Float)

    cell_amount = sa.Column(sa.Float)

    state_id = sa.Column(sa.ForeignKey('specimen_aliquot_term.id'), nullable=False)

    state = orm.relation('SpecimenAliquotTerm', uselist=False, primaryjoin=state_id  == SpecimenAliquotTerm.id)

    store_date = sa.Column(sa.Date)

    freezer = sa.Column(sa.Unicode)

    rack = sa.Column(sa.Unicode)

    box = sa.Column(sa.Unicode)

    storage_site_id = sa.Column(sa.ForeignKey('specimen_aliquot_term.id'), nullable=False)

    storage_site = orm.relation('SpecimenAliquotTerm', uselist=False, primaryjoin=storage_site_id  == SpecimenAliquotTerm.id)

    thawed_num = sa.Column(sa.Integer)

    analysis_status_id = sa.Column(sa.ForeignKey('specimen_aliquot_term.id'), nullable=False)

    analysis_status = orm.relation('SpecimenAliquotTerm', uselist=False, primaryjoin=analysis_status_id == SpecimenAliquotTerm.id,)

    sent_date = sa.Column(sa.Date)

    sent_name = sa.Column(sa.Unicode)

    notes = sa.Column(sa.Unicode)

    special_instruction_id = sa.Column(sa.ForeignKey('specimen_aliquot_term.id'), nullable=False)

    special_instruction = orm.relation('SpecimenAliquotTerm', uselist=False, primaryjoin=special_instruction_id  == SpecimenAliquotTerm.id)

    is_active = sa.Column(sa.Boolean, nullable=False, default=True, index=True)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)


sa.Index('aliquot_specimen_id', Aliquot.specimen_id)
sa.Index('aliquot_type_id', Aliquot.type_id)
sa.Index('aliquot_state_id', Aliquot.state_id)
sa.Index('aliquot_storage_site_id', Aliquot.storage_site_id)
sa.Index('aliquot_analysis_status_id', Aliquot.analysis_status_id)
sa.Index('aliquot_special_instruction_id', Aliquot.special_instruction_id)
