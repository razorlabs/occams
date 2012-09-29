from zope import interface

from sqlalchemy import schema
from sqlalchemy import types
from sqlalchemy import sql
from sqlalchemy import orm
from sqlalchemy import event
from sqlalchemy.ext import declarative
from sqlalchemy.ext import hybrid

from occams.roster import base36
from occams.roster import interfaces


NOW = sql.text('CURRENT_TIMESTAMP')


Model = declarative.declarative_base()


class RosterModel(Model):
    u"""
    Abstract base in case other packages want to use this same base.
    """

    __abstract__ = True

    metadata = schema.MetaData()


class Site(RosterModel):
    interface.implements(interfaces.ISite)

    __doc__ = interfaces.ISite.__doc__

    __tablename__ = 'site'

    id = schema.Column(types.Integer, primary_key=True)

    title = schema.Column(types.Unicode, nullable=False, unique=True)

    create_date = schema.Column(types.DateTime, nullable=False, default=NOW)

    modify_date = schema.Column(types.DateTime, nullable=False, default=NOW, onupdate=NOW)


class Identifier(RosterModel):
    interface.implements(interfaces.IIdentifier)

    __doc__ = interfaces.IIdentifier.__doc__

    __tablename__ = 'identifier'

    id = schema.Column(
        types.Integer,
        schema.Sequence('identifier_id_pk_seq', start=interfaces.START_ID),
        primary_key=True
        )

    origin_id = schema.Column(schema.ForeignKey(Site.id), nullable=False)

    origin = orm.relationship('Site')

    @hybrid.hybrid_property
    def our_number(self):
        encoded = base36.encode(self.id)
        zerofilled = encoded.rjust(6, '0')
        formatted = '%c%c%c-%c%c%c' % tuple(zerofilled)
        return formatted

    @hybrid.hybrid_property
    def value(self):
        return self.id

    is_active = schema.Column(types.Boolean, nullable=False, default=True)

    create_date = schema.Column(types.DateTime, nullable=False, default=NOW)

    modify_date = schema.Column(types.DateTime, nullable=False, default=NOW, onupdate=NOW)

    __table_args__ = dict(sqlite_autoincrement=True)


event.listen(
    Identifier.__table__,
    'after_create', # only do this when the table is created
    schema.DDL(
        'INSERT OR IGNORE INTO sqlite_sequence (name, seq) VALUES (\'identifier\', %d)'
        % interfaces.START_ID
        ).execute_if(dialect='sqlite')
    )


event.listen(
    Identifier.__table__,
    'after_create', # only do this when the table is created
    schema.DDL(
        'ALTER SEQUENCE identifier_id_pk_seq RESTART WITH %d'
        % interfaces.START_ID
        ).execute_if(dialect=['postgresql', 'postgres'])
    )

