import logging
import zope.i18nmessageid


# Used as a central point for i18n translations
MessageFactory = zope.i18nmessageid.MessageFactory(__name__)

# Central logging utility
Logger = logging.getLogger(__name__)

