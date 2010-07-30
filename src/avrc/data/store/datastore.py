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
from avrc.data.store import _utils
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
    
    fia_dsn = u""
    pii_dsn = u""
    
    _pii_engine = None
    _fia_engine = None
    
    store = {}
    
    def __init__(self, fia_dsn, pii_dsn=None):
        """
        """
        self.fia_dsn = fia_dsn
        self.pii_dsn = pii_dsn is None and fia_dsn or pii_dsn
        
        self.schemata = schema.SchemaManager()
        self.protocols = protocol.ProtocolManager()
         
        
    @property
    def binds(self):
        """
        Set up the table-to-engine bindings, this will allow the session
        to handle multiple engines in a session
        """
        binds = {}
        binds.update(dict.fromkeys(model.FIA.metadata.sorted_tables, 
                                   self._fia_engine))
        binds.update(dict.fromkeys(model.PII.metadata.sorted_tables, 
                                   self._pii_engine))
        return binds
    
    def _setup(self):
        """
        Performs data base back-end setup.
        """
        self._fia_engine = sa.create_engine(self.fia_dsn, echo=_ECHO_ENABLED)
        
        if self.fia_dsn == self.pii_dsn:
            self._pii_engine = self._fia_engine
        else:
            self._pii_engine = sa.create_engine(self.pii_dsn, echo=_ECHO_ENABLED)
            
        model.setup_fia(self._fia_engine)
        model.setup_pii(self._pii_engine)
            
    def _unsetup(self):
        """
        Cleans up any data base configurations.
        """
        # Apparently SQLAlchemy doesn't need clean up...
        
    def put(self, visit, obj):
        """
        Store the object into the database based on it's interface
        TODO: Needs tuples/choices/lists and vocabularies...
        """
        provides = list(providedBy(obj))
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
            value_raw = getattr(obj, name)
            
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
        
    def add(self, obj):
        """
        """
        if isinstance(schema.Schema, obj):
            pass
        elif isinstance(protocol.Domain, obj):
            pass
        else:
            # doesn't appear to be a major construct, check it's interface and
            # see we have a schema for it in the DB, if so, this is and
            # instance obj
            raise Exception("WTF")
   
    def get_domain(self, title):
        """
        """
        Session = getUtility(interfaces.ISessionFactory)()
        
        domain_rslt = Session.query(model.Domain)\
                      .filter_by(title=title)\
                      .first()
        
        return protocol.Domain(domain_rslt)
        
    def get_schema(self, title, version=None):
        """
        """
        title = unicode(title)
        version = version is not None and int(version) or None
        Session = getUtility(interfaces.ISessionFactory)()
        
        schema_q = Session.query(model.Schema)\
                      .join(model.Specification)\
                      .filter_by(title=title)
                      
        if version is not None:
            converted = datetime.fromtimestamp(version)
            schema_q = schema_q.filter_by(create_date=converted)
            
        schema_rslt = schema_q.first()
        return schema.Schema(schema_rslt)

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
    
    for t in list(types_factory(None)):
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
    datastore._setup()
    
    SessionUtility = SessionFactory(binds=datastore.binds)
    sm = getSiteManager(datastore)
    sm.registerUtility(SessionUtility, provided=interfaces.ISessionFactory)
    
    setupSupportedTypes()
    
@adapter(interfaces.IDatastore, IObjectRemovedEvent)
def handleDatastoreRemoved(engine, event):
    """
    Triggered when a new DataStore instance is removed from a container
    """
    engine._unsetup()
    sm = getSiteManager(engine)
    sm.registerUtlity(None, provided=interfaces.ISessionFactory)
    
        