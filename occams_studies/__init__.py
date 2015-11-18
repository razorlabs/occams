from __future__ import unicode_literals
import logging
import pkg_resources

from pyramid.i18n import TranslationStringFactory
import wtforms_json; wtforms_json.init()  # monkey-patch wtforms to accept JSON data

from . import models

log = logging.getLogger('occams').getChild(__name__)

_ = TranslationStringFactory(__name__)

__prefix__ = '/studies'
__title__ = _(u'Studies')
__version__ = pkg_resources.require(__name__)[0].version


def initdb(connectable):
    models.StudiesModel.metadata.create_all(connectable)


def includeme(config):

    config.registry.settings['occams.apps']['occams_studies'] = {
        'name': 'studies',
        'title': _(u'Studies'),
        'package': 'occams_studies',
        'route': 'studies.index',
        'version': __version__
    }

    config.include('.assets')
    config.include('.routes')
    config.include('.tasks')
    config.scan()
