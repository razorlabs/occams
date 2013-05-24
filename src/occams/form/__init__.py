import logging

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.i18n import TranslationStringFactory
from sqlalchemy import orm, engine_from_config
from zope.sqlalchemy import ZopeTransactionExtension

from occams.datastore.model import DataStoreSession


__version__ = '1.0.0g1'

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

    config_routes(config)
    config.scan('.views')

    return config.make_wsgi_app()


def config_routes(config):
    """
    Helper method to configure available routes for the application
    """
    config.add_static_view('static', 'static', cache_max_age=3600)

    config.add_route('home', '/')
    config.add_route('about', '/about')
    config.add_route('contact', '/contact')

    config.add_route('account_login', '/login')
    config.add_route('account_logout', '/logout')

    config.add_route('category_add', '/categories/add')
    config.add_route('category_list', '/categories')
    config.add_route('category_view', '/categories/{category_name}')
    config.add_route('category_delete', '/categories/{category_name}/delete')

    config.add_route('form_add', '/add')
    config.add_route('form_view', '/{form_name}')
    config.add_route('form_delete', '/{form_name}/delete')

    config.add_route('version_add', '/{form_name}/add')
    config.add_route('version_view', '/{form_name}/{version}')
    config.add_route('version_edit', '/{form_name}/{version}/edit')
    config.add_route('version_copy', '/{form_name}/{version}/copy')
    config.add_route('version_delete', '/{form_name}/{version}/delete')

    config.add_route('group_add', '/{form_name}/{version}/add')
    config.add_route('group_edit', '/{form_name}/{version}/{group_name}/edit')

    config.add_route('field_add', '/{form_name}/{version}/{group_name}/add')
    config.add_route('field_view', '/{form_name}/{version}/{group_name}/{field_name}')
    config.add_route('field_edit', '/{form_name}/{version}/{group_name}/{field_name}/edit')
    config.add_route('field_move', '/{form_name}/{version}/{group_name}/field_name}/move')
    config.add_route('field_delete', '/{form_name}/{version}/{group_name}/{field_name}/delete')

    return config


def parse_dates(*segment_names):
    """
    Creates function to parse date segments in URL on dispatch.
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

