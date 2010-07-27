"""
Datastore specific library. This module is in charge of handling the
the datastore instances through the use of Object events to keep track of
multiple instances across sites.  
"""
from datetime import datetime

import zope.schema
from zope.component import getUtility
from zope.interface import implements
from zope.interface import providedBy
from zope.i18nmessageid import MessageFactory

import sqlalchemy as sa
    
from avrc.data.store import _model
from avrc.data.store import interfaces
from avrc.data.store import schema
from avrc.data.store import domain

from avrc.data.store.schema import TYPE_MAP

_ = MessageFactory(__name__)

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
        
    @property
    def binds(self):
        # Set up the table-to-engine bindings, this will allow the session
        # to handle multiple engines in a session
        binds = {}
        binds.update(dict.fromkeys(_model.FIA.metadata.sorted_tables, 
                                   self._fia_engine))
        binds.update(dict.fromkeys(_model.PII.metadata.sorted_tables, 
                                   self._pii_engine))
    
    def _setup(self):
        """
        Performs data base back-end setup.
        """
        self._fia_engine = sa.create_engine(self.fia_dsn)
        
        if self.fia_dsn == self.pii_dsn:
            self._pii_engine = self._fia_engine
        else:
            self._pii_engine = sa.create_engine(self.pii_dsn)
            
        _model.setup_fia(self._fia_engine)
        _model.setup_pii(self._pii_engine)
            
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
        schema_rslt = Session.query(_model.Schema)\
                      .join(_model.Specifiation)\
                      .filter_by(title=schema_obj.title)\
                      .first()
                      
        instance_rslt = _model.Instance()
        instance_rslt.schema = schema_rslt
        
        Session.add(instance_rslt)
        
        for name in zope.schema.getNames(provided):
            name = unicode(name)
            attribute_rslt = Session.query(_model.Attribute)\
                             .filter_by(name=name)\
                             .join(_model.Schema)\
                             .filter_by(id=schema_rslt.id)\
                             .first()
            
            value_rslt = None
            value_raw = getattr(obj, name)
            
            if attribute_rslt.type.title in (u"binary",):
                # TODO: unclear how binary values are going to come in
                value_rslt = _model.Binary(value=value_raw)
            elif attribute_rslt.type.title in (u"date", u"time", u"datetime"):
                value_rslt = _model.Datetime(value=value_raw)
            elif attribute_rslt.type.title in (u"integer",):
                value_rslt = _model.Integer(value=value_raw)
            elif attribute_rslt.type.title in (u"object",):
                value_rslt = _model.Object()
                value_rslt.instance = self.put(None, value_raw)
            elif attribute_rslt.type.title in (u"real",):
                value_rslt = _model.Real(value=value_raw)
            elif attribute_rslt.type.title in (u"text", u"string"):
                value_rslt = _model.String(value=value_raw)
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
        elif isinstance(domain.Domain, obj):
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
        
        domain_rslt = Session.query(_model.Domain)\
                      .filter_by(title=title)\
                      .first()
        
        return domain.Domain(domain_rslt)
        
    def get_schema(self, title, version=None):
        """
        """
        title = unicode(title)
        version = version is not None and int(version) or None
        Session = getUtility(interfaces.ISessionFactory)()
        
        schema_q = Session.query(_model.Schema)\
                      .join(_model.Specification)\
                      .filter_by(title=title)
                      
        if version is not None:
            converted = datetime.fromtimestamp(version)
            schema_q = schema_q.filter_by(create_date=converted)
            
        schema_rslt = schema_q.first()
        return schema.Schema(schema_rslt)
        