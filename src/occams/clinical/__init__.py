import logging

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.i18n import TranslationStringFactory
from pyramid.path import DottedNameResolver
from pyramid.security import has_permission
from pyramid_ldap import groupfinder
from sqlalchemy import engine_from_config

# wake up!
import occams.form

from .assets import config_assets
from .models import Session, RosterSession
from .permissions import make_root_factory, make_get_user
from .routes import config_routes


_ = TranslationStringFactory(__name__)

log = logging.getLogger(__name__)


def main(global_config, **settings):
    """
    This function returns a Pyramid WSGI application.
    """
    Session.configure(bind=engine_from_config(settings, 'clinicaldb.'))
    RosterSession.configure(bind=engine_from_config(settings, 'rosterdb.'))

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
        authorization_policy=ACLAuthorizationPolicy())

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

    config_assets(config)

    config.include('pyramid_rewrite')
    config.add_rewrite_rule(r'/(?P<path>.*)/', r'/%(path)s')

    config_routes(config)

    get_user = make_get_user(
        settings['ldap.user.userid_attr'],
        settings['ldap.user.name_attr'])

    config.add_request_method(get_user,'user', reify=True)

    # Wrap has_permission to make it less cumbersome
    config.add_request_method(
        lambda r, n: has_permission(n, r.context, r),
        'has_permission')

    return config.make_wsgi_app()


