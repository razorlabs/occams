""" Anti-Retroviral Medication Models
"""

from datetime import datetime

from sqlalchemy.schema import Column
from sqlalchemy.schema import ForeignKey
from sqlalchemy.types import Boolean
from sqlalchemy.types import Date
from sqlalchemy.types import DateTime
from sqlalchemy.types import Float
from sqlalchemy.types import Integer
from sqlalchemy.types import Unicode

from sqlalchemy.orm import relation as Relationship

from avrc.data.store.model import Model
from avrc.data.store.model.clinical import Subject
from avrc.data.store.model.clinical import Visit


__all__ = ('DrugCategory', 'DrugStatus', 'Drug', 'DrugName', 'Medication',)


class DrugCategory(Model):
    """ A lookup table for drug category values.
        These will be assigned to a specific drug.
    """

    __tablename__ = 'drug_category'

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


class DrugStatus(Model):
    """ A lookup table for drug statuses.
    """

    __tablename__ = 'drug_status'

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


class Drug(Model):
    """ A known drug.
    """

    __tablename__ = 'drug'

    id = Column(Integer, primary_key=True)

    code = Column(Unicode, nullable=False, unique=True)

    recommended_dose = Column(Float)

    drug_category_id = Column(
        ForeignKey(DrugCategory.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    category = Relationship('DrugCategory')

    drug_status_id = Column(
        ForeignKey(DrugStatus.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    status = Relationship('DrugStatus')

    names = Relationship(
        'DrugName',
        primaryjoin='and_(Drug.id==DrugName.drug_id, DrugName.is_active==True)',
        order_by='asc(DrugName.order)'
        )

    is_active = Column(Boolean, nullable=False, default=True, index=True)

    create_date = Column(DateTime, nullable=False, default=datetime.now)

    modify_date = Column(
         DateTime,
         nullable=False,
         default=datetime.now,
         onupdate=datetime.now
         )


class DrugName(Model):
    """ Child table of drug.
        This will contain known names of the drug.
    """

    __tablename__ = 'drug_name'

    id = Column(Integer, primary_key=True)

    drug_id = Column(
        ForeignKey(Drug.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    drug = Relationship('Drug')

    value = Column(Unicode, nullable=False, index=True)

    order = Column(Integer, nullable=False)

    is_active = Column(Boolean, nullable=False, default=True, index=True)

    create_date = Column(DateTime, nullable=False, default=datetime.now)

    modify_date = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now
        )


class Medication(Model):
    """ A period of time in which the subject is taking a drug.
    """

    __tablename__ = 'medication'

    id = Column(Integer, primary_key=True)

    subject_id = Column(
        ForeignKey(Subject.id, ondelete='CASCADE'),
        nullable=False,
        index=True
        )

    subject = Relationship('Subject')

    visit_id = Column(ForeignKey(Visit.id, ondelete='SET NULL'), index=True)

    visit = Relationship('Visit')

    drug_id = Column(
        ForeignKey(Drug.id, ondelete='CASCADE'),
        nullable=False,
        index=True,
        )

    drug = Relationship('Drug')

    start_date = Column(Date, nullable=False)

    stop_date = Column(Date)

    dose = Column(Float)

    notes = Column(Unicode)

    is_active = Column(Boolean, nullable=False, default=True, index=True)

    create_date = Column(DateTime, nullable=False, default=datetime.now)

    modify_date = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now
        )
