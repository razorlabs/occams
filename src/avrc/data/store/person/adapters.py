"""
"""

from zope.interface import implements
from zope.component import adapts

from avrc.data.store import _model
from avrc.data.store.person import interfaces

class ReferenceName(object):
    """
    Translates a reference into a name
    """
    implements(interfaces.IName)
    adapts(interfaces.IReference)
    
    def __init__(self, context):
        self.reference = context
        
    @property
    def first(self):
        return None
    
    @property
    def last(self):
        return None
    
    @property
    def middle(self):
        return None
    
    @property
    def sur(self):
        return None