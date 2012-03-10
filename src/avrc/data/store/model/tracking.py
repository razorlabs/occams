"""
User tracking definitions
"""

import threading

from sqlalchemy import text
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship as Relationship
from sqlalchemy.schema import Column
from sqlalchemy.schema import CheckConstraint
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.schema import Index
from sqlalchemy.schema import ForeignKey
from sqlalchemy.types import Enum
from sqlalchemy.types import DateTime
from sqlalchemy.types import String
from sqlalchemy.types import Unicode

from avrc.data.store.model._meta import Model
from avrc.data.store.model._meta import Referenceable


NOW = text('CURRENT_TIMESTAMP')

trackingRegistry = threading.local()
trackingRegistry.user = None

def setActiveUser(user):
    trackingRegistry.user = user


def getActiveUser():
    return trackingRegistry.user


def clearActiveUser():
    trackingRegistry.user = None


class User(Model, Referenceable):

    email = Column(String, nullable=False)

    fullname = Column(Unicode, nullable=False)

    create_date = Column(DateTime, nullable=False, server_default=NOW)

    modify_date = Column(DateTime, nullable=False, server_default=NOW, onupdate=NOW)

    __table_args = (
        UniqueConstraint('email'),
        CheckConstraint('create_date <= modify_date', 'ck_user_valid_timeline'),
        )


class Log(Model, Referenceable):

    user_id = Column(ForeignKey(User.id), nullable=False)

    user = Relationship('User')

    action = Column(
        Enum('add', 'update', 'delete', name='feed_action'),
        nullable=False
        )

    previous = Column(Unicode)

    current = Column(Unicode)

    log_date = Column(DateTime, nullable=False, server_default=NOW)


def buildModifiableConstraints(cls):
    """
    Returns constrains for modifiable columns, tailored for the specified class

    There doesn't seem to be a good way to put this as a ``declared_attr`` of
    ``Modifiable``, dude the difficulty of using ``super`` on ``property``
    decorators. This, though, is a better alternative as opposed to
    copying and pasting the constraints to each class.
    """
    return (
        CheckConstraint(
            'create_date <= modify_date',
            'ck_%s_valid_timeline' % cls.__tablename__
            ),
        Index('ix_%s_create_user_id' % cls.__tablename__, 'create_user_id'),
        Index('ix_%s_modify_user_id' % cls.__tablename__, 'modify_user_id'),
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
        return Column(ForeignKey(User.id), nullable=False, default=getActiveUser)

    @declared_attr
    def modify_date(cls):
        return Column(DateTime, nullable=False, server_default=NOW, onupdate=NOW)

    @declared_attr
    def modify_user_id(cls):
        return Column(ForeignKey(User.id), nullable=False, default=getActiveUser)
