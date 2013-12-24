"""
Permission constants
All permissions are declared here for easier overview
"""

from repoze.who.interfaces import IChallengeDecider
from pyramid.security import Allow, Authenticated, ALL_PERMISSIONS
from zope.interface import directlyProvides


def challenge_decider(environ, status, headers):
    """
    Repoze.who expects 401, but pyramid will raise 403 when FORBIDDEN
    """
    return status.startswith('403') or status.startswith('401')
directlyProvides(challenge_decider, IChallengeDecider)


class RootFactory(object):

    __acl__ = [
        (Allow, Authenticated, 'view'),
        (Allow, 'admin', ALL_PERMISSIONS)
        ]

    def __init__(self, request):
        self.request = request


class User(object):

    def __init__(self, email, first_name, last_name):
        self.email = email
        self.first_name = first_name
        self.last_name = last_name


def pydb2user(result):
    return User(*result[0])


def ldap2user(result):
    return User(result['mail'], result['cn'], result['sn'])


def groupfinder(identity, request):
    return ['admin']
