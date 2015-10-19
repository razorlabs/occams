import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
import zope.sqlalchemy

import occams_datastore.models.events

from . import log


def includeme(config):
    """
    Configures database connection
    """
    settings = config.registry.settings

    maker = sessionmaker()
    zope.sqlalchemy.register(maker)
    occams_datastore.models.events.register(maker)

    engine = sa.engine_from_config(settings, 'occams.db.')
    maker.configure(bind=engine)

    config.registry['db_sessionmaker'] = maker
    config.add_request_method(_get_db_session, 'db_session', reify=True)

    log.info('Connected to: "%s"' % repr(engine.url))


def _get_db_session(request):
    db_session = request.registry['db_sessionmaker']()
    # Keep track of the request so we can generate model URLs
    db_session.info['request'] = request
    db_session.info['settings'] = request.registry.settings
    return db_session
