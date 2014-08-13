"""
Permission constants
All permissions are declared here for easier overview
"""

from pyramid.events import subscriber, NewRequest
from pyramid.security import Allow, Authenticated, ALL_PERMISSIONS
import wtforms.csrf.core

from . import log, Session


class CSRF(wtforms.csrf.core.CSRF):
    """
    Generates CSRF tokens for WTForms in Pyramid
    """
    def setup_form(self, form):
        self.csrf_context = form.meta.csrf_context
        return super(CSRF, self).setup_form(form)

    def generate_csrf_token(self, csrf_token):
        return self.csrf_context.get_csrf_token()

    def validate_csrf_token(self, form, field):
        if field.data != field.current_token:
            raise ValueError('Invalid CSRF')


def groupfinder(identity, request):
    """
    Pass-through for groups
    """

    if 'groups' not in identity:
        log.warn('groups has not been set in the repoze identity!')
    return identity['groups']


def occams_groupfinder(identity, request):
    """
    Occams-specific group parsing
    """
    if 'groups' not in identity:
        log.warn('groups has not been set in the repoze identity!')

    def parse_group(name):
        parts = name.split('-')
        try:
            org, site, group = parts
        except ValueError:
            org, group = parts
        return group

    return [parse_group(n) for n in identity['groups']]


@subscriber(NewRequest)
def track_user_on_request(event):
    """
    Annotates the database session with the current user.
    """
    request = event.request
    # Keep track of the request so we can generate model URLs
    Session.info['request'] = request
    Session.info['user'] = request.authenticated_userid

    # Store the CSRF token in a cookie since we'll need to sent it back
    # frequently in single-page views.
    # https://docs.djangoproject.com/en/dev/ref/contrib/csrf/
    # The attacker cannot read or change the value of the cookie due to the
    # same-origin policy, and thus cannot guess the right GET/POST parameter
    request.response.set_cookie('csrf_token', request.session.get_csrf_token())


class RootFactory(object):

    __acl__ = [
        (Allow, 'administrator', ALL_PERMISSIONS),
        (Allow, 'consumer', ('fia_view',)),
        (Allow, Authenticated, ('view',)),
        ]

    def __init__(self, request):
        self.request = request


class SiteFactory(object):
    # TODO: future location of per-site access
    pass
