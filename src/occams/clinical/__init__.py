import logging
import pkg_resources

from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.i18n import TranslationStringFactory
from pyramid_who.whov2 import WhoV2AuthenticationPolicy
from repoze.who.config import make_middleware_with_config
from zope.dottedname.resolve import resolve

from occams.clinical.models import Session, RosterSession  # NOQA

__version__ = pkg_resources.require(__name__)[0].version

_ = TranslationStringFactory(__name__)

log = logging.getLogger(__name__)


def main(global_config, **settings):
    """
    This function returns a Pyramid WSGI application.
    """

    config = Configurator(
        settings=settings,
        root_factory='.resources.RootFactory',
        authentication_policy=WhoV2AuthenticationPolicy(
            settings['who.config_file'],
            settings['who.identifier_id'],
            resolve(settings.get('who.callback',
                                 'occams.clinical.auth.groupfinder'))),
        authorization_policy=ACLAuthorizationPolicy())

    config.include('.assets')
    config.include('.tasks')
    config.include('.links')
    config.include('.models')
    config.include('.routes')
    config.include('occams.form.widgets')
    config.scan()
    config.commit()

    app = config.make_wsgi_app()
    who_config = settings['who.config_file']
    app = make_middleware_with_config(app, global_config, who_config)

    log.info('Ready')

    return app
