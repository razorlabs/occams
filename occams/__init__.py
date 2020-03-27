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
    config.include('pyramid_session_redis')
    config.include('pyramid_webassets')
    config.add_renderer('json', JSON(
        adapters=(
            (decimal.Decimal, lambda obj, req: str(obj)),
            (datetime.datetime, lambda obj, req: obj.isoformat()),
            (datetime.date, lambda obj, req: obj.isoformat())
        )),
    )

    config.include('.assets')
    config.include('.models')
    config.include('.routes')
    config.include('.tasks')
    config.include('.security')
    config.scan()

    app = config.make_wsgi_app()

    return app
