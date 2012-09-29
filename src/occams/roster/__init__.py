
import logging
Logger = logging.getLogger(__name__)

import zope.i18nmessageid
MessageFactory = zope.i18nmessageid.MessageFactory(__name__)

from z3c import saconfig
Session = saconfig.named_scoped_session('occams.roster.Session')

