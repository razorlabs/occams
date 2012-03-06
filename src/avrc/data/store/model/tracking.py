"""
"""

from sqlalchemy import case
from sqlalchemy import cast
from sqlalchemy import text
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.schema import Column
from sqlalchemy.schema import CheckConstraint
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.schema import Index
from sqlalchemy.schema import ForeignKey
from sqlalchemy.types import Date
from sqlalchemy.types import DateTime
from sqlalchemy.types import String
from sqlalchemy.types import Unicode

from avrc.data.store.model._meta import Model
from avrc.data.store.model._meta import Referenceable

NOW = text('CURRENT_TIMESTAMP')


class User(Model, Referenceable):

    email = Column(String, nullable=False)

    fullname = Column(Unicode, nullable=False)

    create_date = Column(DateTime, nullable=False, server_default=NOW)

    modify_date = Column(DateTime, nullable=False, server_default=NOW, onupdate=NOW)

    __table_args = (
        UniqueConstraint('email'),
        CheckConstraint('create_date <= modify_date', 'ck_user_valid_timeline'),
        )


class Modifiable(object):
    """
    Adds user edit modification meta data for lifecycle tracking.
    """

    @declared_attr
    def create_date(cls):
        return Column(DateTime, nullable=False, server_default=NOW)

    @declared_attr
    def create_user_id(cls):
        return Column(ForeignKey(User.id), nullable=False)

    @declared_attr
    def modify_date(cls):
        return Column(DateTime, nullable=False, server_default=NOW, onupdate=NOW)

    @declared_attr
    def modify_user_id(cls):
        return Column(ForeignKey(User.id), nullable=False)

    @declared_attr
    def remove_date(cls):
        return Column(DateTime)

    @declared_attr
    def remove_user_id(cls):
        return Column(ForeignKey(User.id))

    @declared_attr
    def __table_args__(self):
        return (
            CheckConstraint(
                'create_date <= modify_date AND modify_date <= remove_date',
                '%s_valid_timeline' % self.__tablename__
                ),
            Index('ix_%s_create_user_id' % self.__tablename__, 'create_user_id'),
            Index('ix_%s_modify_user_id' % self.__tablename__, 'modify_user_id'),
            Index('ix_%s_remove_user_id' % self.__tablename__, 'remove_user_id'),
            Index('ix_%s_remove_date' % self.__tablename__, 'remove_date'),
            )

    @classmethod
    def asOf(cls, on):
        """
        Helper method to generate timeline filter

        Arguments
            ``on``
                A `datetime` object to to check against. A filter that checks
                if ``on`` falls between `create_date` <= `on` < `remove_date`
                will be returned. A value of `None` indicates the most
                recent value should be checked for:
                `create_date` <= `on` < `infinity`
        """
        filter = (None == cls.remove_date)
        if on is not None:
            after_create = (cast(on, Date) >= cast(cls.create_date, Date))
            before_remove = (cast(on, Date) < cast(cls.remove_date, Date))
            during = after_create & before_remove
            filter = case([(filter, after_create)], else_=during)
        return filter
