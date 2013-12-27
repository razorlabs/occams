try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import logging
import pkg_resources

from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.i18n import TranslationStringFactory
from pyramid.path import DottedNameResolver
from pyramid_who.whov2 import WhoV2AuthenticationPolicy
from repoze.who.config import make_middleware_with_config
from sqlalchemy import orm, engine_from_config

from occams.datastore.model import DataStoreSession

__version__ = pkg_resources.require(__name__)[0].version

_ = TranslationStringFactory(__name__)

log = logging.getLogger(__name__)

Session = orm.scoped_session(orm.sessionmaker(
    user=lambda: 'ghost@shell',
    class_=DataStoreSession))


def main(global_config, **settings):
    """
    This function returns a Pyramid WSGI application.
    """
    log.debug('Initializing configuration...')
    config = Configurator(
        settings=settings,
        root_factory='occams.form.auth.RootFactory',
        authentication_policy=WhoV2AuthenticationPolicy(
            settings.get('who.config_file'),
            settings.get('who.auth_tkt'),
            callback=DottedNameResolver().maybe_resolve(
                settings.get('who.callback'))),
        authorization_policy=ACLAuthorizationPolicy())

    log.debug('Connecting to database...')
    Session.configure(bind=engine_from_config(settings, 'sqlalchemy.'))

    apps = make_app_listing(settings.get('apps.config_file'))

    config.add_request_method(
        lambda r: apps,
        name='apps',
        reify=True)

    log.debug('Loading components...')
    config.include('occams.form.assets')
    config.include('occams.form.auth')
    config.include('occams.form.routes')
    config.include('occams.form.widgets')
    config.commit()

    log.debug('Loading middleware...')
    app = config.make_wsgi_app()
    app = make_middleware_with_config(
        app,
        global_config,
        settings.get('who.config_file'))

    return app


def make_app_listing(file_name):
    """
    Generates a listing of additional services as specified in the config file.

    Parameters:
    file_name -- The config file specifing external services

    Returns:
    A listing of dictionaries.
    """
    config = configparser.SafeConfigParser()
    config.read(file_name)
    listing = []

    if not config.has_section('main'):
        return listing

    for suite_name in config.get('main', 'suites').split():
        suite_section = 'suite:' + suite_name
        suite = {
            'name': suite_name,
            'title': config.get(suite_section, 'title'),
            'apps': [],
            }
        for app_name in config.get(suite_section, 'apps', '').split():
            app_section = 'app:' + app_name
            app = {
                'name': app_name,
                'title': config.get(app_section, 'title'),
                'url': config.get(app_section, 'url')}
            suite['apps'].append(app)
        listing.append(suite)

    return listing
