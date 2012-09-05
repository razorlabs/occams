"""
Data entry functionality
"""
from five import grok
from zope.interface import implements
import zope.component
from occams.form import interfaces

from sqlalchemy.orm import object_session

import zope.interface
def _entity_context_cache_key(method, self):
    return self.item.id

def _entity_data_cache_key(method, self):
    return self.item.modify_date

class EntityMovedEvent(zope.component.interfaces.ObjectEvent):
    """Event to notify that entities have been saved.
    """
    implements(interfaces.IEntityMovedEvent)

    def __init__(self, context, object):
        self.context = context
        self.object = object
        self.session = object_session(context)
