"""
Permission constants
All permissions are declared here for easier overview
"""

from repoze.who.interfaces import IChallengeDecider
from pyramid.events import subscriber, NewRequest
from pyramid.security import Allow, Authenticated, ALL_PERMISSIONS
from zope.interface import directlyProvides

from . import log, Session, models


def challenge_decider(environ, status, headers):
    """
    Backwards-compatibility fix to trigger challenge an authorized user.

    Repoze.who expects a status code of 401 to trigger the challenge UI,
    but pyramid will only raise 403 when the user has not authenticated.
    """
    return status.startswith('403') or status.startswith('401')


directlyProvides(challenge_decider, IChallengeDecider)


def groupfinder(identity, request):
    if 'groups' not in identity:
        log.warn('groups has not been set in the repoze identity!')
    return identity.get('groups', [])


def occams_groupfinder(identity, request):

    if 'groups' not in identity:
        log.warn('groups has not been set in the repoze identity!')

    # TODO: move to externa bitcore auth module
    mapping = {
        'aeh-admin': 'administrator',
        'aeh-nurses': 'nurse',
        'aeh-primary_investigators': 'primariy_investicagor'}

    groups = [mapping[g] for g in identity.get('groups', [])]
    return groups


@subscriber(NewRequest)
def track_user_on_request(event):
    """
    Annotates the database session with the current user.
    """
    track_user(event.request.authenticated_userid)


def track_user(userid):
    """
    Helper function to add a user to the database
    """

    if not userid:
        return

    if not Session.query(models.User).filter_by(key=userid).count():
        Session.add(models.User(key=userid))

    # update the current scoped session's infor attribute
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
