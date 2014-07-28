import json
import logging
import pkg_resources

from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.i18n import TranslationStringFactory
from pyramid.path import DottedNameResolver
from pyramid_who.whov2 import WhoV2AuthenticationPolicy
from sqlalchemy import orm, engine_from_config
from webassets import Bundle
import zope.sqlalchemy

import occams.datastore.models.events

__version__ = pkg_resources.require(__name__)[0].version

_ = TranslationStringFactory(__name__)

log = logging.getLogger(__name__)

Session = orm.scoped_session(orm.sessionmaker())

zope.sqlalchemy.register(Session)
occams.datastore.models.events.register(Session)


def main(global_config, **settings):
    """
    Returns initialized WSGI application
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
    config.include('pyramid_tm')

    config.include(assets)
    config.include(links)
    config.include(routes)

    config.scan()
    config.commit()

    app = config.make_wsgi_app()

    log.info('Ready')

    return app


def links(config):
    """
    Configures application links
    """
    file = config.registry.settings.get('suite.file')
    if file:
        with open(file) as fp:
            apps = json.load(fp)
            config.add_request_method(lambda r: apps, name='apps', reify=True)


def assets(config):
    """
    Configures static assets
    """
    config.include('pyramid_webassets')
    config.add_webasset('default-js', Bundle(
        Bundle('libs/jquery.min.js'),
        Bundle('libs/jquery-ui.min.js'),
        Bundle('libs/jquery.cookie.js'),
        Bundle('libs/bootstrap/dist/js/bootstrap.min.js'),
        Bundle('libs/knockout.min.js'),
        Bundle('libs/knockout.mapping.min.js'),
        Bundle('libs/knockout-sortable.min.js'),
        Bundle('libs/select2.min.js'),
        Bundle('libs/moment.min.js'),
        Bundle('libs/bootstrap-datetimepicker/build/js/bootstrap-datetimepicker.min.js'),
        Bundle(
            'scripts/binding-fade-visible.js',
            'scripts/binding-modal.js',
            'scripts/binding-scrolltoif.js',
            'scripts/binding-select2.js',
            'scripts/binding-validateable.js',
            'scripts/form-list.js',
            'scripts/version-edit.js',
            'scripts/version.js',
            'scripts/global.js',
            filters='jsmin'),
        output='gen/default.%(version)s.min.js'))

    config.add_webasset('default-css', Bundle(
        Bundle(
            'styles/main.less',
            filters='less,cssmin',
            depends='styles/*.less',
            output='gen/main.%(version)s.min.css'),
        Bundle('libs/select2.css', filters=['cssmin', 'cssrewrite']),
        Bundle('libs/select2-bootstrap.css', filters='cssmin'),
        output='gen/default.%(version)s.css'))


def routes(config):
    """
    Configures URL routes
    """
    config.include('pyramid_rewrite')
    config.add_rewrite_rule(r'/(?P<path>.*)/', r'/%(path)s')

    config.add_static_view('static', 'static', cache_max_age=3600)

    config.add_route('login',              '/login')
    config.add_route('logout',             '/logout')

    config.add_route('form_list',          '/')
    config.add_route('form_add',           '/forms/add')

    config.add_route('widget_list',        '/widgets')

    config.add_route('version_view',       '/forms/{form}/versions/{version}')
    config.add_route('version_edit',       '/forms/{form}/versions/{version}/edit')
    config.add_route('version_json',       '/forms/{form}/versions/{version}/json')
    config.add_route('version_pdf',        '/forms/{form}/versions/{version}/pdf')
    config.add_route('version_preview',    '/forms/{form}/versions/{version}/preview')

    config.add_route('field_list',         '/forms/{form}/versions/{version}/fields')
    config.add_route('field_view',         '/forms/{form}/versions/{version}/fields/{field}')

    config.add_route('workflow_view',      '/workflows/{workflow}')
