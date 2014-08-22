"""
Permission constants
All permissions are declared here for easier overview
"""

from parse import compile
from pyramid.events import subscriber, NewRequest
from pyramid.settings import aslist
from pyramid.security import Allow, Authenticated, ALL_PERMISSIONS
from sqlalchemy import orm

from . import log, Session, models


def includeme(config):
    """
    Configures additional security utilities
    """
    assert 'auth.groups' in config.registry.settings
    patterns = aslist(config.registry.settings['auth.groups'])
    compiled = [compile(p) for p in patterns]
    config.add_request_method(
        lambda request: compiled, name='group_patterns', reify=True)


def principal(**kw):
    """
    Generates the principal name used internally by this application
    Supported keyword parameters are:
        org -- The organization code
        site --  The site code
        group -- The group name
    """
    return ('{group}:{site}' if 'site' in kw else '{group}').format(**kw)


def groupfinder(identity, request):
    """
    Occams-specific group parsing
    """
    assert 'groups' in identity, \
        'Groups has not been set in the repoze identity!'
    groups = []
    for group in identity['groups']:
        result = None
        for pattern in request.group_patterns:
            result = pattern.parse(group)
            if result:
                groups.append(principal(**result.named))
                break
        if result is None:
            log.warn('Could not find a pattern for %s' % group)
    return groups


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
        (Allow, principal(group='administrator'), ALL_PERMISSIONS),
        (Allow, principal(group='manager'), (
            'export',
            'study_view', 'study_add', 'study_edit', 'study_delete',
            'cycle_view', 'cycle_add', 'cycle_edit', 'cycle_delete',
            'site_view', 'site_add', 'site_edit', 'site_delete')),
        (Allow, principal(group='consumer'), (
            'export',
            'fia_view')),
        (Allow, Authenticated, (
            'study_view',
            'cycle_view',
            'site_view',
            'view'))
        ]

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        """
        When viewing a patient, active site-level permissions

        Idea from:
        http://michael.merickel.org/projects/pyramid_auth_demo/object_security.html
        """
        try:
            site = (
                Session.query(models.Site)
                .join(models.Patient)
                .filter_by(pid=key)
                .one())
        except orm.exc.NoResultFound:
            raise KeyError

        name = site.name
        site.__parent__ = self
        site.__name__ = name
        site.__acl__ = [
            (Allow, principal(site=name, group='manager'), (
                'patient_view', 'patient_add', 'patient_edit',
                'patient_delete',
                'enrollment_view', 'enrollment_add', 'enrollment_edit',
                'enrollment_delete',
                'enrollment_randomize', 'enrollment_terminate'
                'visit_view', 'visit_add', 'visit_edit', 'visit_delete'
                'fia_view', 'fia_add', 'fia_edit', 'fia_delete',
                'phi_view', 'phi_add', 'phi_edit', 'phi_delete'
                )),

            (Allow, principal(site=name, group='reviewer'), (
                'patient_view', 'patient_add', 'patient_edit',
                'patient_delete',
                'enrollment_view', 'enrollment_add', 'enrollment_edit',
                'enrollment_delete',
                'enrollment_randomize', 'enrollment_terminate'
                'visit_view', 'visit_add', 'visit_edit', 'visit_delete'
                'fia_view', 'fia_add', 'fia_edit', 'fia_delete',
                'phi_view', 'phi_add', 'phi_edit', 'phi_delete',
                )),

            (Allow, principal(site=name, group='enterer'), (
                'patient_view', 'patient_add', 'patient_edit',
                'patient_delete',
                'enrollment_view', 'enrollment_add', 'enrollment_edit',
                'enrollment_delete',
                'visit_view', 'visit_add', 'visit_edit', 'visit_delete',
                'fia_view', 'fia_add', 'fia_edit', 'fia_delete',
                'phi_view', 'phi_add', 'phi_edit', 'phi_delete',
                )),

            (Allow, principal(site=name, group='consumer'), (
                'patient_view',
                'enrollment_view',
                'visit_view',
                'fia_view',
                'phi_view',
                )),
            ]

        return site
