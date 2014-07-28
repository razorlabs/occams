"""
Permission constants
all permissions are declared here for easier overview
"""

from pyramid.events import subscriber, NewRequest
from pyramid.security import Allow, Authenticated, ALL_PERMISSIONS

from . import log, Session


def groupfinder(identity, request):

    if 'groups' not in identity:
        log.warn('groups has not been set in the repoze identity!')

    return identity.get('groups', [])


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
def setup_request(event):
    request = event.request

    # Annotates the database session with the current user.
    Session.info['user'] = request.authenticated_userid

    # Store the CSRF token in a cookie since we'll need to sent it back
    # frequently in single-page views.
    # https://docs.djangoproject.com/en/dev/ref/contrib/csrf/
    # The attacker cannot read or change the value of the cookie due to the
    # same-origin policy, and thus cannot guess the right GET/POST parameter
    request.response.set_cookie('csrf_token', request.session.get_csrf_token())


class RootFactory(object):
    """
    Default root that enforces application permissions.

    Client applications with their own principles should define
    their own ``who.callback`` that maps client groups to application
    groups.
    """

    __acl__ = [
        (Allow, 'administrator', ALL_PERMISSIONS),
        (Allow, 'manager', (
            'form_view', 'form_add', 'form_edit', 'form_delete',
            'form_amend', 'form_retract', 'form_publish',
            'workflow_view', 'workflow_add', 'work_edit', 'workflow_delete',
            )),
        (Allow, 'editor', (
            'form_view', 'form_add', 'form_edit', 'form_delete',
            )),
        (Allow, Authenticated, 'view'),
    ]

    def __init__(self, request):
        self.request = request
