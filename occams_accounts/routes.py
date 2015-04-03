# flake8: NOQA
from . import log


def includeme(config):
    """
    Helper method to configure available routes for the application
    """
    config.add_static_view('/accounts/static',   'occams_accounts:static', cache_max_age=3600)
    config.add_route('accounts.main',  '/accounts')
    config.add_route('accounts.login',  '/accounts/login')
    config.add_route('accounts.logout', '/accounts/logout')
    log.debug('Routes configured')
