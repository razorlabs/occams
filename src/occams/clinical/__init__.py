import logging
from pkg_resources import resource_filename

import deform
from redis import StrictRedis
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.i18n import TranslationStringFactory
from pyramid.path import DottedNameResolver
from pyramid.security import has_permission
from pyramid_ldap import groupfinder
from sqlalchemy import engine_from_config
from webassets.loaders import YAMLLoader

from occams.clinical.models import Session, RosterSession
from occams.clinical.permissions import make_root_factory, make_get_user
from occams.form.widgets import DEFAULT_RENDERER


_ = TranslationStringFactory(__name__)

log = logging.getLogger(__name__)

redis = StrictRedis()


def main(global_config, **settings):
    """
    This function returns a Pyramid WSGI application.
    """
    oc_engine = engine_from_config(settings, 'clinicaldb.')
    rt_engine = engine_from_config(settings, 'rosterdb.')

    Session.configure(bind=oc_engine)
    RosterSession.configure(bind=rt_engine)

    config = Configurator(
        settings=settings,
        root_factory=make_root_factory(settings),
        authentication_policy=AuthTktAuthenticationPolicy(
            secret=settings['auth.secret'],
            hashalg=settings['auth.hashalg'],
            timeout=int(settings['auth.timeout']),
            reissue_time=int(settings['auth.reissue_time']),
            http_only=True,
            callback=groupfinder),
        authorization_policy=ACLAuthorizationPolicy()
    )

    config.ldap_setup(
        settings['ldap.setup.host'],
        bind=settings['ldap.setup.bind'],
        passwd=settings['ldap.setup.passwd'],
        timeout=int(settings['ldap.setup.timeout']))
    config.ldap_set_login_query(
        base_dn=settings['ldap.user.base_dn'],
        filter_tmpl=settings['ldap.user.filter_tmpl'].format(percent='%'),
        scope=DottedNameResolver().resolve(settings['ldap.user.scope']))
    config.ldap_set_groups_query(
        base_dn=settings['ldap.group.base_dn'],
        filter_tmpl=settings['ldap.group.filter_tmpl'].format(percent='%'),
        scope=DottedNameResolver().resolve(settings['ldap.group.scope']),
        cache_period=int(settings['ldap.group.cache_period']))

    loader = YAMLLoader(resource_filename('occams.clinical', 'assets.yml'))
    bundles = loader.load_bundles()
    map(lambda i: config.add_webasset(*i), bundles.items())

    config.include('pyramid_rewrite')
    config.add_rewrite_rule(r'/(?P<path>.*)/', r'/%(path)s')

    # builtins views (move to core)
    config.add_route('account_login', '/login')
    config.add_route('account_logout', '/logout')
    config.add_route('account', '/account')
    config.add_route('apps', '/apps')

    # instnance-wide views
    config.add_route('socketio', '/socket.io/*remaining')

    # app-specific views
    config.include('.routes')

    config.scan()

    deform.Form.set_default_renderer(DEFAULT_RENDERER)

    get_user = make_get_user(
        settings['ldap.user.userid_attr'],
        settings['ldap.user.name_attr'])

    config.add_request_method(get_user, 'user', reify=True)

    # Wrap has_permission to make it less cumbersome
    # TODO: This is built-in to pyramid 1.5, remove when we switch
    def has_permission_wrap(request, name):
        return has_permission(name, request.context, request)

    config.add_request_method(has_permission_wrap, 'has_permission')

    return config.make_wsgi_app()
