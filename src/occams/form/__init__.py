import logging

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.i18n import TranslationStringFactory
from sqlalchemy import orm, engine_from_config
from zope.sqlalchemy import ZopeTransactionExtension

from occams.datastore.model import DataStoreSession

__version__ = '1.0.0g1'

TranslationString = TranslationStringFactory(__name__)

# XXX Used as a central point for i18n translations
import zope.i18nmessageid
MessageFactory = zope.i18nmessageid.MessageFactory(__name__)

# Central logging utility
Logger = logging.getLogger(__name__)

Session = orm.scoped_session(orm.sessionmaker(
    user=lambda: 'ghost@shell',
    class_=DataStoreSession,
    extension=ZopeTransactionExtension()))


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    Session.configure(bind=engine_from_config(settings, 'sqlalchemy.'))

    # Start'er up
    config = Configurator(
        settings=settings)

    config.include('pyramid_rewrite')
    config.add_rewrite_rule(r'/(?P<path>.*)/', r'/%(path)s')

    # Bind URLs
    config_routes(config)
    config.scan('occams.form.views.form')

    app = config.make_wsgi_app()
    return app


def config_routes(config):
    """ Helper method to configure available routes for the application
    """
    config.add_static_view('static', 'static', cache_max_age=3600)

    config.add_route('form_list', '/forms')
    config.add_route('form_view', '/forms/{form_name}')

    return config


def parse_dates(*segment_names):
    """ Creates function to parse date segments in URL on dispatch.
    """
    def predicate(info, request):
        match = info['match']
        for segment_name in segment_names:
            try:
                raw = match[segment_name]
                parsed = datetime.datetime.strptime(raw, '%Y-%m-%d').date()
                match[segment_name] = parsed
            except ValueError:
                return False
        return True
    return predicate

