import logging
import pkg_resources

from pyramid.i18n import TranslationStringFactory
import wtforms_json

from occams import Session

wtforms_json.init()  # monkey-patch wtforms to accept JSON data

log = logging.getLogger(__name__)

_ = TranslationStringFactory(__name__)

__prefix__ = '/forms'
__title__ = _(u'Forms')
__version__ = pkg_resources.require(__name__)[0].version


def includeme(config):
    config.include('.assets')
    config.include('.routes')
    config.scan()
