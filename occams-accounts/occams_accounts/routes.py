# flake8: NOQA
from . import log


def includeme(config):
    """
    Helper method to configure available routes for the application
    """
    config.add_static_view(path='occams_accounts:static', name='/static', cache_max_age=3600)
    config.add_route('accounts.index',  '/')
    config.add_route('accounts.login',  '/login')
    config.add_route('accounts.logout', '/logout')
    log.debug('Routes configured')
