"""
Permission constants
All permissions are declared here for easier overview
"""

from repoze.who.interfaces import IChallengeDecider
from pyramid.security import (
    has_permission, Allow, Authenticated, ALL_PERMISSIONS)
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

    @property
    def fullname(self):
        return self.first_name + ' ' + self.last_name


def pydb2user(result):
    return User(*result[0])


def ldap2user(result):
    return User(result['mail'], result['cn'], result['sn'])


def groupfinder(identity, request):
    return ['admin']


def includeme(config):
    user = User('foobatio@localhost', 'Foo', 'Bario')
    config.add_request_method(lambda r: user, 'user', reify=True)

    # Wrap has_permission to make it less cumbersome
    # TODO: This is built-in to pyramid 1.5, remove when we switch
    def has_permission_wrap(request, name):
        return has_permission(name, request.context, request)

    config.add_request_method(has_permission_wrap, 'has_permission')

    return config
