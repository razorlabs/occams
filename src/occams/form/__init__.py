import logging
import zope.i18nmessageid


__version__ = '1.0.0g1'


# Used as a central point for i18n translations
MessageFactory = zope.i18nmessageid.MessageFactory(__name__)

# Central logging utility
Logger = logging.getLogger(__name__)

