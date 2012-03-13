"""
Data store primary classes and modules
"""

import logging
import zope.i18nmessageid


# Used as a central point for i18n translations
MessageFactory = zope.i18nmessageid.MessageFactory(__name__)

# Central logging utility
Logger = logging.getLogger(__name__)


from occams.datastore.managers import DataStore
from occams.datastore.managers import SchemaManager
from occams.datastore.managers import AttributeManager
from occams.datastore.managers import HierarchyInspector
from occams.datastore.managers import EntityManager
from occams.datastore.managers import ValueManager
#from occams.datastore.managers import ObjectFactory

