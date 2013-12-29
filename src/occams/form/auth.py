"""
Permission constants
All permissions are declared here for easier overview
"""

from repoze.who.interfaces import IChallengeDecider
from pyramid.security import (
    has_permission, Allow, Authenticated, ALL_PERMISSIONS)
from zope.interface import directlyProvides

from occams.form import log


def challenge_decider(environ, status, headers):
    """
    Backwards-compatibility fix to trigger challenge an authorized user.

    Repoze.who expects a status code of 401 to trigger the challenge UI,
    but pyramid will only raise 403 when the user has not authenticated.
    """
    return status.startswith('403') or status.startswith('401')


directlyProvides(challenge_decider, IChallengeDecider)


class RootFactory(object):

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


def list2properties(results):
    return dict(zip(('email', 'first_name', 'last_name'), results[0]))


def list2groups(results):
    return [name for (name,) in results]


def ldap2user(result):
    return {
        'email': result['mail'],
        'first_name': result['cn'],
        'last_name': result['sn']}


def groupfinder(identity, request):
    if 'groups' not in identity:
        log.warn('groups has not been set in the repoze identity!')
    return identity.get('groups', [])


def includeme(config):
    log.debug('Initializing auth helpers...')

    # Wrap has_permission to make it less cumbersome
    # TODO: This is built-in to pyramid 1.5, remove when we switch
    config.add_request_method(
        lambda r, n: has_permission(n, r.context, r),
        'has_permission')
