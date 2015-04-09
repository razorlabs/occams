from __future__ import unicode_literals
import logging
import pkg_resources

from pyramid.i18n import TranslationStringFactory

log = logging.getLogger('occams').getChild(__name__)

_ = TranslationStringFactory(__name__)

__prefix__ = '/accounts'
__title__ = _(u'Accounts')
__version__ = pkg_resources.require(__name__)[0].version


def includeme(config):
    # App-specific configurations
    config.include('.assets')
    config.include('.routes')
    config.scan()
