from __future__ import unicode_literals
import decimal
import datetime
import logging
from importlib import import_module
import pkg_resources

import six
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.i18n import TranslationStringFactory
from pyramid.renderers import JSON
from pyramid.settings import aslist
from pyramid_who.whov2 import WhoV2AuthenticationPolicy
from pyramid.settings import asbool
import wtforms_json; wtforms_json.init()

__version__ = pkg_resources.require(__name__)[0].version

_ = TranslationStringFactory(__name__)

log = logging.getLogger(__name__)

from .settings import piwik_from_config
from .security import RootFactory, groupfinder  # NOQA


settings_defaults = {
    'piwik.enabled': False,

    # Ignored unless static_view is set to true
    # static_view needs to be false in order to allow multiple asset locations
    'webassets.base_dir': 'occams:static',
    'webassets.base_url': 'static',
    'webassets.static_view': False,

    'who.callback': 'occams.security.groupfinder'
    }


def main(global_config, **settings):
    """
    This function returns a Pyramid WSGI application.
    """

    # Applies setting defaults if not specified
    for key, value in settings_defaults.items():
        settings.setdefault(key, value)

    # Make sure we at least have te
    apps = aslist(settings.get('occams.apps') or '')
    settings['occams.apps'] = dict.fromkeys(apps)

    settings.update(piwik_from_config(settings))

    # determine if deployment is development
    settings['occams.development'] = asbool(settings.get('occams.development'))

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
    config.include('pyramid_redis')
    config.include('pyramid_redis_sessions')
    config.include('pyramid_tm')
    config.include('pyramid_webassets')
    config.add_renderer('json', JSON(
        adapters=(
            (decimal.Decimal, lambda obj, req: str(obj)),
            (datetime.datetime, lambda obj, req: obj.isoformat()),
            (datetime.date, lambda obj, req: obj.isoformat())
        )),
    )
    config.commit()

    # Main includes
    config.include('.assets')
    config.include('.celery')
    config.include('.models')
    config.include('.routes')
    config.include('.security')
    config.scan()
    config.commit()

    # Application includes

    for name in six.iterkeys(settings['occams.apps']):
        app = import_module(name)
        prefix = getattr(app, '__prefix__', None)
        if not prefix:
            # These should only appear in debug-mode during app development
            log.debug(u'{} does not have a prefix'.format(name))
            config.include(app)
        else:
            config.include(app, route_prefix=prefix)
    config.commit()

    config.add_request_method(_apps, name=str('apps'), reify=True)
    config.commit()

    app = config.make_wsgi_app()

    log.info('Ready')

    return app


def _apps(request):
    all_apps = six.itervalues(request.registry.settings['occams.apps'])
    filtered_apps = iter(a for a in all_apps if a)
    sorted_apps = sorted(filtered_apps, key=lambda f: f['title'])
    return sorted_apps
