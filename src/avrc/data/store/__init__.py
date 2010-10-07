""" Data store primary classes and modules
"""

# Used as a central point for i18n translations
import zope.i18nmessageid
MessageFactory = zope.i18nmessageid.MessageFactory(__name__)

# For defining data store virtual schemata
from avrc.data.store.interfaces import Schema

# Custom type
from avrc.data.store.schema import Range

__all__ = [
    "Range",
    "Schema",
    ]