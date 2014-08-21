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

    def callback(request):
        return compiled

    config.add_request_method(callback, name='group_patterns', reify=True)


def principal(**kw):
    """
    Generates the principal name used internally by this application
    Supported keyword parameters are:
        org -- The organization code
        site --  The site code
        group -- The group name
    """

    if 'site' in kw:
        return '{group}:{site}'.format(**kw)
    else:
        return '{group}'.format(**kw)


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


class PatientFactory(object):

    __acl__ = [
        (Allow, 'administrator', ALL_PERMISSIONS),
        (Allow, 'consumer', ('fia_view',)),
        (Allow, Authenticated, ('view',)),
        ]

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        """
        Find the site and apply object-level security
        """
        try:
            patient = Session.query(models.Patient).filter_by(pid=key).one()
        except orm.exc.NoResultFound:
            raise KeyError

        name = patient.site.name
        patient.__parent__ = self
        patient.__name__ = name
        patient.__acl__ = [
            (Allow, principal(site=name, group='manager'), (
                'export',
                'fia_view', 'fia_add', 'fia_edit', 'fia_delete',
                'phi_view', 'phi_add', 'phi_edit', 'phi_delete',
                'study_view', 'study_add', 'study_edit', 'study_delete',
                'cycle_view', 'cycle_add', 'cycle_edit', 'cycle_delete',
                'site_view', 'site_add', 'site_edit', 'site_delete',
                'patient_view', 'patient_add', 'patient_edit',
                'patient_delete',
                'enrollment_view', 'enrollment_add', 'enrollment_edit',
                'enrollment_delete',
                'enrollment_randomize', 'enrollment_terminate'
                'visit_view', 'visit_add', 'visit_edit', 'visit_delete')),

            (Allow, principal(site=name, group='reviewer'), (
                'fia_view', 'fia_add', 'fia_edit', 'fia_delete',
                'phi_view', 'phi_add', 'phi_edit', 'phi_delete',
                'study_view',
                'cycle_view',
                'site_view',
                'patient_view', 'patient_add', 'patient_edit',
                'patient_delete',
                'enrollment_view', 'enrollment_add', 'enrollment_edit',
                'enrollment_delete',
                'enrollment_randomize', 'enrollment_terminate'
                'visit_view', 'visit_add', 'visit_edit', 'visit_delete')),

            (Allow, principal(site=name, group='enterer'), (
                'fia_view', 'fia_add', 'fia_edit', 'fia_delete',
                'phi_view', 'phi_add', 'phi_edit', 'phi_delete',
                'study_view',
                'cycle_view',
                'site_view',
                'patient_view', 'patient_add', 'patient_edit',
                'patient_delete',
                'enrollment_view', 'enrollment_add', 'enrollment_edit',
                'enrollment_delete',
                'enrollment_randomize', 'enrollment_terminate'
                'visit_view', 'visit_add', 'visit_edit', 'visit_delete')),

            (Allow, principal(site=name, group='consumer'), (
                'export',
                'fia_view',
                'phi_view',
                'study_view',
                'cycle_view',
                'site_view',
                'patient_view',
                'enrollment_view',
                'visit_view')),

            (Allow, principal(site=name, group='member'), ('view',))
            ]

        return patient
