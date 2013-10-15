"""
Permission Components
"""

import ldap

from pyramid_ldap import get_ldap_connector
from pyramid.security import authenticated_userid
from pyramid.security import Allow, Everyone, Authenticated, ALL_PERMISSIONS


def make_root_factory(settings):
    """
    Builds Access Control Lists (ACL) from configuration
    """
    acl = [(Allow, Authenticated, 'view')]

    groups = settings['groups'].split()

    for group in groups:
        permissions = settings['group.{0}.permissions'.format(group)].split()
        dns = settings['group.{0}.dns'.format(group)].split()
        for dn in dns:
            if 'ALL_PERMISSIONS' in permissions:
                acl.append((Allow, dn, ALL_PERMISSIONS))
            else:
                acl.append((Allow, dn, permissions))

    class RootFactory(object):

        def __init__(self, request):
            self.request = request

    RootFactory.__acl__ = acl

    return RootFactory


def make_get_user(userid_attr, name_attr):
    # Use the ldap connector to issue a search query for the exact DN
    # of the user that authenticated.
    def get_user(request):
        if request is None:
            return
        with get_ldap_connector(request).manager.connection() as connection:
            user_dn = authenticated_userid(request)
            if user_dn is None:
                return
            dn, record = connection.search_s(user_dn, ldap.SCOPE_BASE)[0]
            return User(record[userid_attr][0], record[name_attr][0])
    return get_user


class User(object):
    """
    Convenient access of crucial user identification properties
    """

    def __init__(self, email, fullname):
        self.email = email
        self.fullname = fullname

