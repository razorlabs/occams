import logging
import pkg_resources

from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.i18n import TranslationStringFactory
from pyramid.path import DottedNameResolver
from pyramid_who.whov2 import WhoV2AuthenticationPolicy
from sqlalchemy import orm, engine_from_config
import zope.sqlalchemy

import occams.datastore.models.events

from occams.datastore import models  # NOQA

__version__ = pkg_resources.require(__name__)[0].version

_ = TranslationStringFactory(__name__)

log = logging.getLogger(__name__)

# TODO: use ``register`` intstead when it becomes available
Session = orm.scoped_session(orm.sessionmaker(
    extension=zope.sqlalchemy.ZopeTransactionExtension()))
occams.datastore.models.events.register(Session)


def main(global_config, **settings):
    """
    This function returns a Pyramid WSGI application.
    """

    config = Configurator(
        settings=settings,
        root_factory='occams.forms.security.RootFactory',
        authentication_policy=WhoV2AuthenticationPolicy(
            settings.get('who.config_file'),
            settings.get('who.identifier_id'),
            DottedNameResolver().resolve(settings.get('who.callback'))),
        authorization_policy=ACLAuthorizationPolicy())

    Session.configure(bind=engine_from_config(settings, 'sqlalchemy.'))

    config.include('pyramid_chameleon')
    config.include('pyramid_mailer')
    config.include('pyramid_redis_sessions')
    config.include('pyramid_rewrite')
    config.add_rewrite_rule(r'/(?P<path>.*)/', r'/%(path)s')
    config.include('pyramid_tm')
    config.include('pyramid_webassets')

    config.include('.assets')
    config.include('.links')
    config.include('.routes')
    config.scan()
    config.commit()

    app = config.make_wsgi_app()

    log.info('Ready')

    return app
