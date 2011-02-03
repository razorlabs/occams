""" Symptom Library
"""
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import orm

from avrc.data.store.model import Model


class SymptomType(Model):
    """
    """

    __tablename__ = 'symptom_type'

    id = sa.Column(sa.Integer, primary_key=True)

    value = sa.Column(sa.Unicode, nullable=False, index=True)

    is_active = sa.Column(sa.Boolean, nullable=False, default=True, index=True)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)


class Symptom(Model):
    """
    """

    __tablename__ = 'symptom'

    id = sa.Column(sa.Integer, primary_key=True)

    subject_id = sa.Column(sa.ForeignKey('subject.id'), nullable=False, index=True)

    subject = orm.relation('Subject', uselist=False)

    symptom_type_id = sa.Column(sa.ForeignKey('symptom_type.id'), nullable=False, index=True)

    type = orm.relation('SymptomType', uselist=False)

    type_other = sa.Column(sa.Unicode)

    is_attended = sa.Column(sa.Boolean)

    start_date = sa.Column(sa.Date, nullable=False)

    stop_date = sa.Column(sa.Date)

    notes = sa.Column(sa.Unicode)

    is_active = sa.Column(sa.Boolean, nullable=False, default=True, index=True)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)
