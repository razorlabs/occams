from __future__ import unicode_literals
import logging
import pkg_resources

from pyramid.i18n import TranslationStringFactory
import wtforms_json

wtforms_json.init()  # monkey-patch wtforms to accept JSON data

log = logging.getLogger('occams').getChild(__name__)

_ = TranslationStringFactory(__name__)

__version__ = pkg_resources.require(__name__)[0].version


def includeme(config):

    config.registry.settings['occams.apps']['occams_studies'] = {
        'name': 'studies',
        'title': _(u'Studies'),
        'package': 'occams_studies',
        'route': 'studies.main',
        'version': __version__
    }

    config.include('.assets')
    config.include('.routes')
    config.include('.tasks')
    config.scan()
