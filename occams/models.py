import six
import sqlalchemy as sa

from . import Session, log


def includeme(config):
    """
    Configures database connection
    """
    settings = config.registry.settings

    # tests will override the session, use the setting for everything else
    if isinstance(settings['occams.db.url'], six.string_types):
        Session.configure(bind=sa.engine_from_config(settings, 'occams.db.'))

    log.info('Connected to: "%s"' % repr(Session.bind.url))
