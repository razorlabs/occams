# flake8: NOQA
# This module breaks my OCD-ness in favor of readability
from datetime import datetime
from . import log

from . import models


def includeme(config):
    """
    Helper method to configure available routes for the application
    """
    config.add_static_view('static',                'occams.accounts:static', cache_max_age=3600)

    config.add_route('login',                       '/login')
    config.add_route('logout',                      '/logout')
    config.add_route('accounts',                    '/', factory=models.AccountFactory, traverse='/')
    config.add_route('account',                     '/{account}', factory=models.AccountFactory, traverse='/{account}')

    log.debug('Routes configured')
