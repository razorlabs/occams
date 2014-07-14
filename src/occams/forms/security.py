"""
Permission constants
all permissions are declared here for easier overview
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
def track_user_on_request(event):
    """
    Annotates the database session with the current user.
    """
    Session.info['user'] = event.request.authenticated_userid


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
