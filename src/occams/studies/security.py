"""
Permission constants
All permissions are declared here for easier overview
"""

from pyramid.events import subscriber, NewRequest
from pyramid.security import Allow, Authenticated, ALL_PERMISSIONS

from . import log, Session


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
        # return the last part in the list
        return group[-1]

    return [parse_group(n) for n in identity['groups']]


@subscriber(NewRequest)
def track_user_on_request(event):
    """
    Annotates the database session with the current user.
    """
    Session.info['user'] = event.request.authenticated_userid


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
