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
    config = Configurator(
        settings=settings,
        root_factory='occams.form.auth.RootFactory',
        authentication_policy=WhoV2AuthenticationPolicy(
            settings.get('who.config_file'),
            settings.get('who.auth_tkt'),
            callback=DottedNameResolver().maybe_resolve(
                settings.get('who.callback'))),
        authorization_policy=ACLAuthorizationPolicy())

    Session.configure(bind=engine_from_config(settings, 'sqlalchemy.'))

    config.include('occams.form.assets')
    config.include('occams.form.auth')
    config.include('occams.form.routes')
    config.include('occams.form.widgets')
    config.commit()

    app = config.make_wsgi_app()
    app = make_middleware_with_config(
        app,
        global_config,
        settings.get('who.config_file'))

    return app
