"""
Permission constants
All permissions are declared here for easier overview
"""


from repoze.who.interfaces import IChallengeDecider
from pyramid.events import subscriber, NewRequest
from pyramid.security import authenticated_userid
from zope.interface import directlyProvides

from occams.clinical import log, Session, models


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
    track_user(authenticated_userid(event.request))


def track_user(userid):
    """
    Helper function to add a user to the database
    """

    if not userid:
        return

    if not Session.query(models.User).filter_by(key=userid).count():
        Session.add(models.User(key=userid))

    # update the current scoped session's infor attribute
    Session.configure(info={'user': userid})
