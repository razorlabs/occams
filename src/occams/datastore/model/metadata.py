""" Common metadata modules
"""

from sqlalchemy.types import String
from sqlalchemy.types import Unicode
from sqlalchemy.schema import Column
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.declarative import has_inherited_table
from sqlalchemy.types import Integer
from sqlalchemy import text
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import relationship as Relationship
from sqlalchemy.orm import object_session
from sqlalchemy.schema import CheckConstraint
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.schema import ForeignKey
from sqlalchemy.types import DateTime
from zope.interface import implements

from occams.datastore.model import Model
from occams.datastore.interfaces import IUser
from occams.datastore.interfaces import NonExistentUserError


NOW = text('CURRENT_TIMESTAMP')


def updateMetadata(instance, created):
    session = object_session(instance)

    key = session.userCallback()

    try:
        user = session.query(User).filter_by(key=key).one()
    except NoResultFound:
        raise NonExistentUserError(key)

    if created:
        instance.create_user = user

    instance.modify_user = user


class AutoNamed(object):
    """
    Generates the SQL table name from the class name.
    """

    @declared_attr
    def __tablename__(cls):
        if has_inherited_table(cls) and AutoNamed not in cls.__bases__:
            return None
        return cls.__name__.lower()


class Referenceable(object):
    """
    Adds primary key id columns to tables.
    """

    id = Column(Integer, primary_key=True)


class Describeable(object):
    """
    Adds standard content properties to tables.
    """

    name = Column(String, nullable=False)

    title = Column(Unicode, nullable=False)

    description = Column(Unicode)


class User(Model, AutoNamed, Referenceable):
    implements(IUser)

    key = Column(String, nullable=False)

    create_date = Column(DateTime, nullable=False, server_default=NOW)

    modify_date = Column(DateTime, nullable=False, server_default=NOW, onupdate=NOW)

    @declared_attr
    def __table_args__(cls):
        return (
            UniqueConstraint('key', name='uq_%s_key' % cls.__tablename__),
            CheckConstraint(
                'create_date <= modify_date',
                name='ck_%s_valid_timeline' % cls.__tablename__
                ),
            )


class Modifiable(object):
    """
    Adds user edit modification meta data for lifecycle tracking.
    """

    @declared_attr
    def create_date(cls):
        return Column(
            DateTime,
            nullable=False,
            server_default=NOW
            )

    @declared_attr
    def create_user_id(cls):
        return Column(
            Integer,
            ForeignKey(
                'user.id',
                name='fk_%s_create_user_id' % cls.__tablename__,
                ondelete='RESTRICT'
                ),
            nullable=False,
            index=True, # SA Index() still sucks
            )

    @declared_attr
    def create_user(cls):
        return Relationship(User,
            primaryjoin='%s.create_user_id == User.id' % cls.__name__)

    @declared_attr
    def modify_date(cls):
        return Column(
            DateTime,
            CheckConstraint(
                'create_date <= modify_date',
                'ck_%s_valid_timeline' % cls.__tablename__
                ),
            nullable=False,
            server_default=NOW,
            onupdate=NOW
            )

    @declared_attr
    def modify_user_id(cls):
        return Column(
            Integer,
            ForeignKey(
                'user.id',
                name='fk_%s_modify_user_id' % cls.__tablename__,
                ondelete='RESTRICT'
                ),
            nullable=False,
            index=True, # SA Index() still sucks
            )

    @declared_attr
    def modify_user(cls):
        return Relationship(User,
            primaryjoin='%s.modify_user_id == User.id' % cls.__name__)
