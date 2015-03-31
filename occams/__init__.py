from __future__ import unicode_literals
import logging
import pkg_resources

from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.i18n import TranslationStringFactory
from pyramid.path import DottedNameResolver
from pyramid.settings import aslist
from pyramid_who.whov2 import WhoV2AuthenticationPolicy
from sqlalchemy.orm import scoped_session, sessionmaker
import wtforms_json
import zope.sqlalchemy

wtforms_json.init()  # monkey-patch wtforms to accept JSON data

import occams_datastore.models.events

__version__ = pkg_resources.require(__name__)[0].version

_ = TranslationStringFactory(__name__)

log = logging.getLogger(__name__)

Session = scoped_session(sessionmaker(
    extension=zope.sqlalchemy.ZopeTransactionExtension()))
occams_datastore.models.events.register(Session)

from .security import RootFactory, groupfinder  # NOQA

import os

here = os.path.dirname(os.path.realpath(__file__))

settings_defaults = {
    'webassets.base_dir': os.path.join(here, 'static'),
    'webassets.base_url': '/static',

    'who.callback': 'occams.security.groupfinder'
}


def main(global_config, **settings):
    """
    This function returns a Pyramid WSGI application.
    """

    for key, value in settings_defaults.items():
        settings.setdefault(key, value)

    settings['occams.apps'] = set(aslist(settings.get('occams.apps') or ''))
    settings['occams.apps'].update(['occams_datastore', 'occams_accounts'])

    config = Configurator(
        settings=settings,
        root_factory=RootFactory,
        authentication_policy=WhoV2AuthenticationPolicy(
            settings['who.config_file'],
            settings['who.identifier_id'],
            groupfinder),
        authorization_policy=ACLAuthorizationPolicy())

    # Built-in plugins
    config.include('pyramid_chameleon')
    config.include('pyramid_redis_sessions')
    config.include('pyramid_tm')
    config.include('pyramid_webassets')
    config.commit()

    # Main includes
    config.include('.assets')
    config.include('.links')
    config.include('.models')
    config.include('.routes')
    config.include('.security')
    config.commit()
    config.scan()

    # Appliation includes
    resolver = DottedNameResolver()
    for name in settings['occams.apps']:
        app = resolver.maybe_resolve(name)
        prefix = getattr(app, '__prefix__', None)
        if prefix:
            log.debug('Mounting %s at %s' % (name, prefix))
            config.include(app, route_prefix=prefix)
        else:
            log.debug('Mounting %s at /' % name)
            config.include(app)
    config.commit()

    app = config.make_wsgi_app()

    log.info('Ready')

    return app
