"""
Data Manipulation Library
"""

from zope.app.component.hooks import getSite


from z3c.saconfig import SiteScopedSession

    
from avrc.data.store import ddl

# -----------------------------------------------------------------------------
# Engine setup
# -----------------------------------------------------------------------------

def _setup_base(base, engine):
    """
    """
    base.metadata.bind = engine    
    base.metadata.create_all(checkfirst=True)
     
     
def setup_accessible(engine):
    """
    """
    _setup_base(ddl.Accessible, engine)
    
    
def setup_internal(engine):
    """
    """
    _setup_base(ddl.Internal, engine)


# -----------------------------------------------------------------------------
# Session setup
# -----------------------------------------------------------------------------

class StoreSiteScopedSession(SiteScopedSession):
        
    def siteScopeFunc(self):
        return getSite().id
    


    
    
    