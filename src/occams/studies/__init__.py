from datetime import datetime
import json
import logging
import pkg_resources

from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.i18n import TranslationStringFactory
from pyramid.path import DottedNameResolver
from pyramid_who.whov2 import WhoV2AuthenticationPolicy
from sqlalchemy.orm import scoped_session, sessionmaker
from webassets import Bundle
import zope.sqlalchemy

import occams.datastore.models.events

__version__ = pkg_resources.require(__name__)[0].version

_ = TranslationStringFactory(__name__)

log = logging.getLogger(__name__)

Session = scoped_session(sessionmaker(
    extension=zope.sqlalchemy.ZopeTransactionExtension()))
occams.datastore.models.events.register(Session)


def main(global_config, **settings):
    """
    This function returns a Pyramid WSGI application.
    """
    config = Configurator(
        settings=settings,
        root_factory='occams.studies.security.RootFactory',
        authentication_policy=WhoV2AuthenticationPolicy(
            settings['who.config_file'],
            settings['who.identifier_id'],
            DottedNameResolver().maybe_resolve(
                settings.get('who.callback')
                or 'occams.studies.security:groupfinder')),
        authorization_policy=ACLAuthorizationPolicy())

    # Required third-party plugins
    config.include('pyramid_chameleon')
    config.include('pyramid_mailer')
    config.include('pyramid_redis')
    config.include('pyramid_redis_sessions')
    config.include('pyramid_rewrite')
    config.add_rewrite_rule(r'/(?P<path>.*)/', r'/%(path)s')
    config.include('pyramid_tm')
    config.include('pyramid_webassets')

    # Required second-party plugins
    config.include(settings['pid.package'])

    # App-specific configurations
    config.include(assets)
    config.include(links)
    config.include('.models')
    config.include(routes)
    config.include('.tasks')

    config.scan()
    config.commit()

    app = config.make_wsgi_app()

    log.info('Ready')

    return app


def assets(config):
    """
    Loads web assets
    """

    config.add_webasset('default-js', Bundle(
        # Dependency javascript libraries must be loaded in a specific order
        Bundle('libs/jquery.min.js'),
        Bundle('libs/jquery-ui.min.js'),
        Bundle('libs/jquery.cookie.js'),
        Bundle('libs/jquery.validate.min.js'),
        Bundle('libs/bootstrap/dist/js/bootstrap.min.js'),
        Bundle('libs/knockout.min.js'),
        Bundle('libs/knockout.mapping.min.js'),
        Bundle('libs/knockout-sortable.min.js'),
        Bundle('libs/select2.min.js'),
        Bundle('libs/moment.min.js'),
        Bundle('libs/bootstrap-datetimepicker/src/js/bootstrap-datetimepicker.js'),
        #Bundle('libs/bootstrap-datetimepicker/build/js/bootstrap-datetimepicker.min.js'),
        Bundle('libs/sammy.min.js'),
        Bundle('libs/socket.io.min.js'),
        Bundle(
            'scripts/*.js',
            'scripts/**/*.js',
            depends='scripts/**/*.js', filters='jsmin'),
        output='gen/default.%(version)s.min.js'))

    config.add_webasset('default-css', Bundle(
        Bundle(
            'styles/main.less',
            filters='less,cssmin',
            depends='styles/**/*.less',
            output='gen/main.%(version)s.min.css'),
        Bundle('libs/select2.css', filters=['cssmin', 'cssrewrite']),
        Bundle('libs/select2-bootstrap.css', filters='cssmin'),
        output='gen/default.%(version)s.css'))

    log.debug('Assets configurated')


def links(config):
    file = config.registry.settings.get('suite.file')
    apps = None
    if file:
        with open(file) as fp:
            apps = json.load(fp)
    config.add_request_method(lambda r: apps, name='apps', reify=True)
    log.debug('External app listing configured.')


def routes(config):
    """
    Helper method to configure available routes for the application
    """
    ymd = dates('date')

    config.add_static_view('static', 'occams.studies:static/')

    config.add_route('socket.io',           '/socket.io/*remaining')

    config.add_route('login',               '/login')
    config.add_route('logout',              '/logout')

    config.add_route('sites',               '/sites')
    config.add_route('site',                '/sites/{site}')

    config.add_route('reference_types',     '/reference_types')
    config.add_route('reference_type',      '/reference_types/{reference_type}')

    config.add_route('studies',             '/')
    config.add_route('study',               '/studies/{study}')
    config.add_route('study_schedule',      '/studies/{study}/schedule')
    config.add_route('study_ecrfs',         '/studies/{study}/ecrfs')
    config.add_route('study_progress',      '/studies/{study}/progress')

    config.add_route('cycles',              '/studies/{study}/cycles')
    config.add_route('cycle',               '/studies/{study}/cycles/{cycle}')

    config.add_route('patients',            '/patients')
    config.add_route('patient',             '/patients/{patient}')
    config.add_route('patient_forms',       '/patients/{patient}/forms')
    config.add_route('patient_form',        '/patients/{patient}/forms/{form}')
    config.add_route('patient_enrollments', '/patients/{patient}/enrollments')
    config.add_route('patient_visits',      '/patients/{patient}/visits')

    config.add_route('enrollment',          '/enrollments/{enrollment}')
    config.add_route('visit',               '/patients/{patient}/visits/{visit}',
                     custom_predicates=[ymd])

    config.add_route('exports',             '/exports')
    config.add_route('exports_checkout',    '/exports/checkout')
    config.add_route('exports_status',      '/exports/status')
    config.add_route('exports_faq',         '/exports/faq')
    config.add_route('exports_codebook',    '/exports/codebook')
    config.add_route('export',              '/exports/{export:\d+}')
    config.add_route('export_download',     '/exports/{export:\d+}/download')

    config.add_route('home',                '/')

    log.debug('Routes configured')


def dates(*keys):
    """
    Creates function to parse date segments in URL on dispatch.
    """
    def strpdate(str):
        return datetime.strptime(str, '%Y-%m-%d').date()

    def predicate(info, request):
        for key in keys:
            try:
                info['match'][key] = strpdate(info['match'][key])
            except ValueError:
                return False
        return True

    return predicate
