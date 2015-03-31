from __future__ import unicode_literals
import logging
import pkg_resources

from pyramid.i18n import TranslationStringFactory
import wtforms_json

wtforms_json.init()  # monkey-patch wtforms to accept JSON data

from occams import Session

log = logging.getLogger(__name__)

_ = TranslationStringFactory(__name__)

__prefix__ = '/studies'
__title__ = _(u'Studies')
__version__ = pkg_resources.require(__name__)[0].version


def includeme(config):
    config.include('.assets')
    config.include('.routes')
    config.include('.tasks')
    config.scan()
