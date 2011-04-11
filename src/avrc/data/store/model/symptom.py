""" Symptom Models
"""
from datetime import datetime

from sqlalchemy.schema import Column
from sqlalchemy.schema import ForeignKey
from sqlalchemy.types import Boolean
from sqlalchemy.types import Date
from sqlalchemy.types import DateTime
from sqlalchemy.types import Integer
from sqlalchemy.types import Unicode

from sqlalchemy.orm import relation as Relationship

from avrc.data.store.model import Model
from avrc.data.store.model.clinical import Subject


__all__ = ('SymptomType', 'Symptom',)


class SymptomType(Model):
    """
    """

    __tablename__ = 'symptom_type'

    id = Column(Integer, primary_key=True)

    value = Column(Unicode, nullable=False, index=True)

    is_active = Column(Boolean, nullable=False, default=True, index=True)

    create_date = Column(DateTime, nullable=False, default=datetime.now)

    modify_date = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now
        )


class Symptom(Model):
    """
    """

    __tablename__ = 'symptom'

    id = Column(Integer, primary_key=True)

    subject_id = Column(
        ForeignKey(Subject.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    subject = Relationship('Subject')

    symptom_type_id = Column(
        ForeignKey(SymptomType.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    type = Relationship('SymptomType')

    type_other = Column(Unicode)

    is_attended = Column(Boolean)

    start_date = Column(Date, nullable=False)

    stop_date = Column(Date)

    notes = Column(Unicode)

    is_active = Column(Boolean, nullable=False, default=True, index=True)

    create_date = Column(DateTime, nullable=False, default=datetime.now)

    modify_date = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now
        )
