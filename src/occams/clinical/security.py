"""
Permission constants
All permissions are declared here for easier overview
"""

from pyramid.events import subscriber, NewRequest
from pyramid.security import Allow, Authenticated, ALL_PERMISSIONS
from sqlalchemy.orm.exc import NoResultFound

from . import log, Session, models


def groupfinder(identity, request):
    if 'groups' not in identity:
        log.warn('groups has not been set in the repoze identity!')
    return identity.get('groups', [])


def occams_groupfinder(identity, request):
    if 'groups' not in identity:
        log.warn('groups has not been set in the repoze identity!')

    # TODO: move to externa bitcore auth module
    mapping = {
        'aeh-admins': 'administrator',
        'aeh-nurses': 'nurse',
        'aeh-primary_investigators': 'primariy_investicagor'}

    groups = [mapping[g] for g in identity.get('groups', []) if g in mapping]
    return groups


@subscriber(NewRequest)
def track_user_on_request(event):
    """
    Annotates the database session with the current user.
    """
    track_user(event.request.authenticated_userid)


def track_user(userid, is_current=True):
    """
    Helper function to add a user to the database
    """

    if not userid:
        return

    try:
        Session.query(models.User).filter_by(key=userid).one()
    except NoResultFound:
        Session.add(models.User(key=userid))
        Session.flush()

    if is_current:
        Session.info['user'] = userid


class RootFactory(object):

    __acl__ = [
        (Allow, 'administrator', ALL_PERMISSIONS),
        (Allow, 'investigator', (
            'view',
            'fia_view')),
        (Allow, 'coordinator', (
            'view',
            'fia_view')),
        (Allow, 'statistician', (
            'view',
            'fia_view')),
        (Allow, 'researcher', (
            'view',
            'fia_view')),
        (Allow, 'nurse', (
            'view'
            'site_view',
            'patient_add',  'patient_view',  'patient_edit',
            'enrollment_add',  'enrollment_view',  'enrollment_edit',
            'enrollment_delete',
            'visit_add',  'visit_view',  'visit_edit',  'visit_delete',
            'fia_view')),
        (Allow, 'assistant', ('view',)),
        (Allow, 'student', ('view',)),
        (Allow, Authenticated, 'view'),
        ]

    def __init__(self, request):
        self.request = request


class SiteFactory(object):
    # TODO: future location of per-site access
    pass
