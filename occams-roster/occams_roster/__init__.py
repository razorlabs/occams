import logging
import pkg_resources

from alembic.util import obfuscate_url_pw
from sqlalchemy import engine_from_config

__version__ = pkg_resources.require(__name__)[0].version

log = logging.getLogger('occams').getChild(__name__)

from .generator import OUR_PATTERN, generate  # NOQA
from . import models


def includeme(config):
    """
    Include as a pyramid application add-on
    """
    settings = config.registry.settings
    engine = engine_from_config(settings, 'roster.db.')
    config.registry['dbsession_factory'].configure(binds={
        models.Site: engine,
        models.Identifier: engine
    })
    log.debug('Roster connected to: "%s"' % obfuscate_url_pw(engine.url))
