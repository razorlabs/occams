""" Anti-Retroviral Medication Models
"""

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import orm

from avrc.data.store.model import Model


class Drug(Model):
    """ A known drug.
    """

    __tablename__ = 'drug'

    id = sa.Column(sa.Integer, primary_key=True)

    code = sa.Column(sa.Unicode, nullable=False, unique=True)

    recommended_dose = sa.Column(sa.Float)

    drug_category_id = sa.Column(
        sa.ForeignKey('drug_category.id'),
        nullable=False,
        index=True
        )

    category = orm.relation('DrugCategory', uselist=False)

    drug_status_id = sa.Column(
        sa.ForeignKey('drug_status.id'),
        nullable=False,
        index=True
        )

    status = orm.relation('DrugStatus', uselist=False)

    names = orm.relation(
        'DrugName',
        primaryjoin='and_(Drug.id==DrugName.drug_id, DrugName.is_active==True)',
        order_by='asc(DrugName.order)'
        )

    is_active = sa.Column(sa.Boolean, nullable=False, default=True, index=True)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)


class DrugName(Model):
    """ Child table of drug.
        This will contain known names of the drug.
    """

    __tablename__ = 'drug_name'

    id = sa.Column(sa.Integer, primary_key=True)

    drug_id = sa.Column(
        sa.ForeignKey('drug.id'),
        nullable=False,
        index=True
        )

    drug = orm.relation('Drug', uselist=False)

    value = sa.Column(sa.Unicode, nullable=False, index=True)

    order = sa.Column(sa.Integer, nullable=False)

    is_active = sa.Column(sa.Boolean, nullable=False, default=True, index=True)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)


class DrugCategory(Model):
    """ A lookup table for drug category values.
        These will be assigned to a specific drug.
    """

    __tablename__ = 'drug_category'

    id = sa.Column(sa.Integer, primary_key=True)

    value = sa.Column(sa.Unicode, nullable=False, index=True)

    is_active = sa.Column(sa.Boolean, nullable=False, default=True, index=True)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)


class DrugStatus(Model):
    """ A lookup table for drug statuses.
    """

    __tablename__ = 'drug_status'

    id = sa.Column(sa.Integer, primary_key=True)

    value = sa.Column(sa.Unicode, nullable=False, index=True)

    is_active = sa.Column(sa.Boolean, nullable=False, default=True, index=True)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)


class Medication(Model):
    """ A period of time in which the subject is taking a drug.
    """

    __tablename__ = 'medication'

    id = sa.Column(sa.Integer, primary_key=True)

    subject_id = sa.Column(
        sa.ForeignKey('subject.id'),
        nullable=False,
        index=True
        )

    subject = orm.relation('Subject', uselist=False)

    visit_id = sa.Column(
        sa.ForeignKey('visit.id'),
        index=True
        )

    visit = orm.relation('Visit', uselist=False)

    drug_id = sa.Column(
        sa.ForeignKey('drug.id'),
        nullable=False,
        index=True
        )

    drug = orm.relation('Drug', uselist=False)

    start_date = sa.Column(sa.Date, nullable=False)

    stop_date = sa.Column(sa.Date)

    dose = sa.Column(sa.Float)

    notes = sa.Column(sa.Unicode)

    is_active = sa.Column(sa.Boolean, nullable=False, default=True, index=True)

    create_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now)

    modify_date = sa.Column(sa.DateTime, nullable=False, default=datetime.now,
                            onupdate=datetime.now)
