import logging
import pkg_resources

from pyramid.i18n import TranslationStringFactory
import wtforms_json; wtforms_json.init()  # monkey-patch wtforms to accept JSON data

log = logging.getLogger('occams').getChild(__name__)

_ = TranslationStringFactory(__name__)

__prefix__ = '/forms'
__title__ = _(u'Forms')
__version__ = pkg_resources.require(__name__)[0].version


def includeme(config):

    config.registry.settings['occams.apps']['occams_forms'] = {
        'name': 'forms',
        'title': _(u'Forms'),
        'package': 'occams_forms',
        'route': 'forms.index',
        'version': __version__
    }

    config.include('.assets')
    config.include('.routes')
    config.scan()
