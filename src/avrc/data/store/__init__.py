""" Data store primary classes and modules
"""

import zope.i18nmessageid.MessageFactory

__all__ = [
    "MessageFactory",
    "Schema"
    ]

# Used as a central point for i18n translations
MessageFactory = zope.i18nmessageid.MessageFactory(__name__)

# For defining data store virtual schemata
from avrc.data.store.interfaces import Schema
