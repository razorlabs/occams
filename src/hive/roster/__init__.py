
import logging
from z3c.saconfig import named_scoped_session
import zope.i18nmessageid

Logger = logging.getLogger(__name__)

MessageFactory = zope.i18nmessageid.MessageFactory(__name__)

Session = named_scoped_session('hive.roster.Session')

from hive.roster.factory import OurNumberFactory
