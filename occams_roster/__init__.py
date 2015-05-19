import logging
import pkg_resources

from alembic.util import obfuscate_url_pw
from sqlalchemy import engine_from_config
from sqlalchemy.orm import scoped_session, sessionmaker
import zope.sqlalchemy


__version__ = pkg_resources.require(__name__)[0].version

log = logging.getLogger('occams').getChild(__name__)

Session = scoped_session(sessionmaker(
    extension=zope.sqlalchemy.ZopeTransactionExtension()))

from .generator import OUR_PATTERN, generate  # NOQA


def includeme(config):
    """
    Include as a pyramid application add-on
    """
    settings = config.registry.settings
    Session.configure(bind=engine_from_config(settings, 'roster.db.'))
    log.debug('Roster connected to: "%s"'
              % obfuscate_url_pw(Session.bind.url))
