""" Data store primary classes and modules
"""

import logging
import zope.i18nmessageid

# Used as a central point for i18n translations
MessageFactory = zope.i18nmessageid.MessageFactory(__name__)

# Central logging utility
Logger = logging.getLogger(__name__)

#
# We declare exposed functionality here, after everything has been initialized
#

from avrc.data.store.datastore import Datastore


# For defining data store virtual schemata
from avrc.data.store.interfaces import Schema

