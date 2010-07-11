
from zope import component
from zope.app.component.hooks import getSite

import zope.site

from z3c.saconfig import SiteScopedSession
from z3c.saconfig import EngineFactory
from z3c.saconfig.interfaces import IScopedSession

from collective.saconnect.interfaces import ISQLAlchemyConnectionStrings

from avrc.data.store import database

class StoreSiteScopedSession(SiteScopedSession):
    def siteScopeFunc(self):
        return getSite().id

def initialize(context):
    """
    Initializer called when used as a Zope 2 product.
    """
    
    
@component.adapter(zope.site.interfaces.INewLocalSite)
def siteSetup(event):
    print
    print
    print event
    print
    print
    
#    connections = ISQLAlchemyConnectionStrings(getSite())
#    
#    fia_engine = EngineFactory(connections["fia"])
#    pii_engine = EngineFactory(connections["pii"])
#    
#    Session = StoreSiteScopedSession()
#    
#    binds = {}
#    
#    fia_tables = getattr(database.Accessible.metadata, "sorted_tables")
#    pii_tables = getattr(database.Internal.metadata, "sorted_tables")
#    
#    binds.update(dict.fromkeys(fia_tables, fia_engine))
#    binds.update(dict.fromkeys(pii_tables, pii_engine))
#    
#    Session.configure(binds=binds)
#    
#    component.provideUtility(Session, 
#                             provides=IScopedSession)
    
    