"""
This module is in charge of handling the
the datastore instances through the use of Object events to keep track of
multiple instances across sites.
"""
from datetime import datetime

import zope.schema
from zope.component import createObject
from zope.component import getUtility
from zope.component import adapter
from zope.component import getSiteManager
from zope.component.factory import Factory
from zope.interface import implements
from zope.interface import providedBy
from zope.i18nmessageid import MessageFactory
from zope.lifecycleevent import IObjectAddedEvent
from zope.lifecycleevent import IObjectRemovedEvent

import sqlalchemy as sa
from sqlalchemy import orm

from avrc.data.store import model
from avrc.data.store import interfaces
from avrc.data.store import schema
from avrc.data.store import protocol

_ = MessageFactory(__name__)

_ECHO_ENABLED = True

class Datastore(object):
    """
    """
    implements(interfaces.IDatastore)

    __name__ = None
    __parent__ = None

    title = None
    dsn = None

    def __init__(self, title, dsn):
        """
        """
        self.title = title
        self.dsn = dsn

    @property
    def schemata(self):
        return schema.SchemaManager()

    @property
    def protocols(self):
        return protocol.ProtocolManager()
    
    def has(self, key):
        """
        """
    
    def get(self, key):
        """
        """
        
    def keys(self):
        """
        """
        raise NotImplementedError("This method is not implemented")

    def put(self, target):
        """
        Store the object into the database based on it's interface
        TODO: Needs choices and lists/tuples/sets
        """
        provides = list(target.__provides__)
        Session = getUtility(interfaces.ISessionFactory)()

        if len(provides) > 1:
            raise Exception("Only one interface at a time supported.")

        if len(provides) < 1:
            raise Exception("Object does not provide an interface.")

        provided = provides.pop()
        schema_obj = interfaces.ISchema(provided)

        #
        # TODO: VERSIONING>!!>!>!
        #
        schema_rslt = Session.query(model.Schema)\
                      .join(model.Specification)\
                      .filter_by(title=schema_obj.title)\
                      .first()

        instance_rslt = model.Instance()
        instance_rslt.schema = schema_rslt

        Session.add(instance_rslt)

        for name in zope.schema.getFieldNamesInOrder(provided):
            name = unicode(name)
            attribute_rslt = Session.query(model.Attribute)\
                             .filter_by(name=name)\
                             .join(model.Schema)\
                             .filter_by(id=schema_rslt.id)\
                             .first()

            value_rslt = None
            value_raw = getattr(target, name)

            if attribute_rslt.type.title in (u"binary",):
                # TODO: unclear how binary values are going to come in
                value_rslt = model.Binary(value=value_raw)
            elif attribute_rslt.type.title in (u"date", u"time", u"datetime"):
                value_rslt = model.Datetime(value=value_raw)
            elif attribute_rslt.type.title in (u"integer",):
                value_rslt = model.Integer(value=value_raw)
            elif attribute_rslt.type.title in (u"object",):
                value_rslt = model.Object()
                value_rslt.instance = self.put(None, value_raw)
            elif attribute_rslt.type.title in (u"real",):
                value_rslt = model.Real(value=value_raw)
            elif attribute_rslt.type.title in (u"text", u"string"):
                value_rslt = model.String(value=value_raw)
            else:
                raise Exception("Type %s unsupported."  % repr(provided[name]))

            value_rslt.attribute = attribute_rslt
            value_rslt.instance = instance_rslt

            Session.add(value_rslt)

        Session.commit()

DatastoreFactory = Factory(
    Datastore,
    title=_(u"Data store factory"),
    description=_(u"Does stuff")
    )

class SessionFactory(object):
    """
    @see avrc.data.store.interfaces.ISessionFactory
    TODO: This module might have some issue with nested Sessions... this might
    need to be fixed on a per request basis. (using scoped_session maybe?)
    """

    implements(interfaces.ISessionFactory)

    def __init__(self,
                 autocommit=False,
                 autoflush=True,
                 twophase=False,
                 bind=None,
                 binds=None):
        """
        Our ISessionFactory implementation takes an extra parameter which
        will be the database bindings.
        """
        self.autocommit = autocommit
        self.autoflush = autoflush
        self.twophase = twophase
        self.binds = binds
        self.bind = bind

    def __call__(self):
        """
        Creates the Session object and binds it to the appropriate databases.
        @see: avrc.data.store.interfaces.ISessionFactory#__call__
        """

        Session  = orm.scoped_session(orm.sessionmaker(
            autocommit=self.autocommit,
            autoflush=self.autoflush,
            twophase=self.twophase
            ))

        Session.configure(bind=self.bind, binds=self.binds)

        return Session

def setupSupportedTypes():
    """
    This method should be used when setting up the supported types for a
    Datastore content type being added to a folder in the zope site.
    """
    rslt = []
    Session = getUtility(interfaces.ISessionFactory)()
    types_factory = getUtility(zope.schema.interfaces.IVocabularyFactory,
                               name="avrc.data.store.SupportedTypes")

    for t in list(types_factory()):
        rslt.append(model.Type(
            title=unicode(t.token),
            description=unicode(getattr(t.value, "__doc__", None)),
            ))

    Session.add_all(rslt)
    Session.commit()

@adapter(interfaces.IDatastore, IObjectAddedEvent)
def handleDatastoreAdded(datastore, event):
    """
    Triggered when a new DataStore instance is added to a container (i.e.
    when it is added to a site.
    This method will setup all metadata needed for the engine to fully
    offer it's services.
    """    
    engine = sa.create_engine(datastore.dsn, echo=True)

    # Set autocommit true so that components create their own sessions.
    sm = getSiteManager(datastore)
    sm.registerUtility(SessionFactory(bind=engine), 
                       provided=interfaces.ISessionFactory)

    setupSupportedTypes()

@adapter(interfaces.IDatastore, IObjectRemovedEvent)
def handleDatastoreRemoved(datastore, event):
    """
    Triggered when a new DataStore instance is removed from a container
    """
    sm = getSiteManager(datastore)
    sm.registerUtlity(None, provided=interfaces.ISessionFactory)

