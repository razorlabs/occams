from zope.interface import implements

from sqlalchemy.schema import Column
from sqlalchemy.schema import ForeignKey
from sqlalchemy.schema import Sequence
from sqlalchemy.types import Boolean
from sqlalchemy.types import DateTime
from sqlalchemy.types import Integer
from sqlalchemy.types import Unicode
from sqlalchemy.sql import text
from sqlalchemy.orm import relation as Relationship
from sqlalchemy.ext.declarative import synonym_for
from sqlalchemy.ext.declarative import declarative_base

from hive.roster.base36 import base36encode
from hive.roster.interfaces import ISite
from hive.roster.interfaces import IIdentifier
from hive.roster.interfaces import START_ID


NOW = text('CURRENT_TIMESTAMP')

Model = declarative_base()


class Site(Model):
    implements(ISite)

    __tablename__ = 'site'

    id = Column(Integer, primary_key=True)

    title = Column(Unicode, nullable=False, unique=True)

    create_date = Column(DateTime, nullable=False, default=NOW)

    modify_date = Column(DateTime, nullable=False, default=NOW, onupdate=NOW)


class Identifier(Model):
    implements(IIdentifier)

    __tablename__ = 'identifier'

    id = Column(Integer, Sequence('identifier_id_pk_seq', start=START_ID), primary_key=True)

    origin_id = Column(ForeignKey(Site.id), nullable=False)

    origin = Relationship('Site')

    @synonym_for('id')
    @property
    def value(self):
        return self.id

    is_active = Column(Boolean, nullable=False, default=True)

    create_date = Column(DateTime, nullable=False, default=NOW)

    modify_date = Column(DateTime, nullable=False, default=NOW, onupdate=NOW)

    __table_args__ = (
        None,
        dict(sqlite_autoincrement=True),
        )

    def __str__(self):
        encoded = base36encode(self.id)
        zerofilled = encoded.rjust(6, '0')
        formatted = '%c%c%c-%c%c%c' % tuple(zerofilled)
        return formatted
