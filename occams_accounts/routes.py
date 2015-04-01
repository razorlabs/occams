# flake8: NOQA
from . import log


def includeme(config):
    """
    Helper method to configure available routes for the application
    """
    config.add_static_view('/static', 'occams_accounts:static', cache_max_age=3600)
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    log.debug('Routes configured')
