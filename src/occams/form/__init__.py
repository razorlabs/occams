import logging
from pkg_resources import resource_filename

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.i18n import TranslationStringFactory
from sqlalchemy import orm, engine_from_config
from zope.sqlalchemy import ZopeTransactionExtension

from occams.datastore.model import DataStoreSession

from .assets import config_assets
from .routes import config_routes

__version__ = '2.0.0'

_ = TranslationStringFactory(__name__)

Logger = logging.getLogger(__name__)

Session = orm.scoped_session(orm.sessionmaker(
    user=lambda: 'ghost@shell',
    class_=DataStoreSession,
    extension=ZopeTransactionExtension()))


def main(global_config, **settings):
    """
    This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)

    Session.configure(bind=engine_from_config(settings, 'sqlalchemy.'))

    config.include('pyramid_rewrite')
    config.add_rewrite_rule(r'/(?P<path>.*)/', r'/%(path)s')

    config_assets(config)
    config_routes(config).scan('.views')

    return config.make_wsgi_app()



