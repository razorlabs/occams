""" Lab Models
"""

from datetime import datetime

from sqlalchemy.schema import Column
from sqlalchemy.schema import ForeignKey
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.types import Boolean
from sqlalchemy.types import Date
from sqlalchemy.types import DateTime
from sqlalchemy.types import Float
from sqlalchemy.types import Integer
from sqlalchemy.types import Time
from sqlalchemy.types import Unicode

from sqlalchemy.orm import relation as Relationship

from avrc.data.store.model import Model
from avrc.data.store.model.clinical import Protocol
from avrc.data.store.model.clinical import Subject


__all__ = ('SpecimenAliquotTerm', 'Specimen', 'Aliquot', 'AliquotHistory',)


class SpecimenAliquotTerm(Model):
    """
    . . .
    """
    __tablename__ = 'specimen_aliquot_term'

    id = Column(Integer, primary_key=True)

    vocabulary_name = Column(Unicode, nullable=False, index=True)

    title = Column(Unicode)

    token = Column(Unicode, nullable=False)

    value = Column(Unicode, nullable=False)

    is_active = Column(Boolean, nullable=False, default=True, index=True)

    create_date = Column(DateTime, nullable=False, default=datetime.now)

    modify_date = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now
        )

    __table_args = (
        UniqueConstraint('vocabulary_name', 'token', 'value'),
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

    id = Column(Integer, primary_key=True)

    subject_id = Column(
        ForeignKey(Subject.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    subject = Relationship('Subject')

    protocol_id = Column(
        ForeignKey(Protocol.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    protocol = Relationship('Protocol')

    state_id = Column(
        ForeignKey(SpecimenAliquotTerm.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    state = Relationship(
        'SpecimenAliquotTerm',
        primaryjoin=state_id == SpecimenAliquotTerm.id
        )

    collect_date = Column(Date)

    collect_time = Column(Time)

    type_id = Column(
        ForeignKey(SpecimenAliquotTerm.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    type = Relationship(
        'SpecimenAliquotTerm',
        primaryjoin=type_id == SpecimenAliquotTerm.id
        )

    destination_id = Column(
        ForeignKey(SpecimenAliquotTerm.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    destination = Relationship(
        'SpecimenAliquotTerm',
        primaryjoin=destination_id == SpecimenAliquotTerm.id
        )

    tubes = Column(Integer)

    tupe_type_id = Column(
        ForeignKey(SpecimenAliquotTerm.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    tube_type = Relationship(
         'SpecimenAliquotTerm',
         primaryjoin=tupe_type_id == SpecimenAliquotTerm.id
         )

    notes = Column(Unicode)

    aliquot = Relationship('Aliquot')

    create_name = Column(Unicode(255))

    modify_name = Column(Unicode(255))

    study_cycle_label = Column(Unicode(255))

    is_active = Column(Boolean, nullable=False, default=True, index=True)

    create_date = Column(DateTime, nullable=False, default=datetime.now)

    modify_date = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now
        )

    __table_args = (
        UniqueConstraint('subject_id', 'protocol_id', 'type'),
        {})


class Aliquot(Model):
    """ Specialized table for aliquot parts generated from a specimen.

        Attributes:
            id: (int) machine generated primary key
            specimen_id: (int) the specimen this aliquot was generated from
    """
    __tablename__ = 'aliquot'

    id = Column(Integer, primary_key=True)

    specimen_id = Column(
        ForeignKey(Specimen.id, ondelete='CASCADE'),
        nullable=False,
        index=True,
        )

    specimen = Relationship('Specimen')

    type_id = Column(
        ForeignKey(SpecimenAliquotTerm.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    type = Relationship(
        'SpecimenAliquotTerm',
        primaryjoin=type_id == SpecimenAliquotTerm.id
        )

    volume = Column(Float)

    cell_amount = Column(Float)

    state_id = Column(
        ForeignKey(SpecimenAliquotTerm.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    state = Relationship(
        'SpecimenAliquotTerm',
        primaryjoin=state_id == SpecimenAliquotTerm.id
        )

    store_date = Column(Date)

    freezer = Column(Unicode)

    rack = Column(Unicode)

    box = Column(Unicode)

    storage_site_id = Column(
        ForeignKey(SpecimenAliquotTerm.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    storage_site = Relationship(
        'SpecimenAliquotTerm',
        primaryjoin=storage_site_id == SpecimenAliquotTerm.id
        )

    thawed_num = Column(Integer)

    analysis_status_id = Column(
        ForeignKey(SpecimenAliquotTerm.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    analysis_status = Relationship(
        'SpecimenAliquotTerm',
        primaryjoin=analysis_status_id == SpecimenAliquotTerm.id,
        )

    sent_date = Column(Date)

    sent_name = Column(Unicode)

    notes = Column(Unicode)

    special_instruction_id = Column(
        ForeignKey(SpecimenAliquotTerm.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    special_instruction = Relationship(
        'SpecimenAliquotTerm',
        primaryjoin=special_instruction_id == SpecimenAliquotTerm.id
        )

    create_name = Column(Unicode(255))

    modify_name = Column(Unicode(255))

    is_active = Column(Boolean, nullable=False, default=True, index=True)

    create_date = Column(DateTime, nullable=False, default=datetime.now)

    modify_date = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now
        )


class AliquotHistory(Model):
    """ Keeps track of aliquot state history.
    """

    __tablename__ = 'aliquot_history'

    id = Column(Integer, primary_key=True)

    aliquot_id = Column(
        ForeignKey(Aliquot.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    state_id = Column(
        ForeignKey(SpecimenAliquotTerm.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    state = Relationship(
        'SpecimenAliquotTerm',
        primaryjoin=state_id == SpecimenAliquotTerm.id
        )

    action_date = Column(DateTime, nullable=False)

    to = Column(Unicode, nullable=False)

