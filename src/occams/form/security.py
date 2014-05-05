"""
Permission constants
all permissions are declared here for easier overview
"""

from pyramid.events import subscriber, NewRequest
from pyramid.security import Allow, Authenticated, ALL_PERMISSIONS
from sqlalchemy.orm.exc import NoResultFound

from occams.form import log, Session, models


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

    # TODO: move to externa bitcore auth module

    mapping = {
        'admins': 'administrator',
        'nurses': 'nurse',
        'primary_investigators': 'primariy_investigator'}

    def parse_group(name):
        parts = name.split('-')
        try:
            org, site, group = parts
        except ValueError:
            org, group = parts
        if group in mapping:
            return mapping[group]
        else:
            return name

    return [parse_group(n) for n in identity['groups']]


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
    """
    Default root that enforces application permissions.

    Client applications with their own principles should define
    their own ``who.callback`` that maps client groups to application
    groups.
    """

    __acl__ = [
        (Allow, 'administrator', ALL_PERMISSIONS),
        (Allow, 'manager', (
            'form_add', 'form_edit', 'form_delete',
            'form_amend', 'form_retract', 'form_publish',
            'form_export',
            'workflow_add', 'work_edit', 'workflow_delete',
            )),
        (Allow, 'editor', (
            'form_add', 'form_edit', 'form_delete',
            'form_export',
            )),
        (Allow, Authenticated, 'view'),
    ]

    def __init__(self, request):
        self.request = request
