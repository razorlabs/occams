from pyramid.settings import aslist
from pyramid.security import Allow, Authenticated
import six
import sqlalchemy as sa
from sqlalchemy import orm

from occams.datastore.models import User   # NOQA

from . import Session, log


def includeme(config):
    """
    Configures additional security utilities
    """
    settings = config.registry.settings

    assert 'auth.groups' in settings

    mappings = {}

    for entry in aslist(settings['auth.groups'], flatten=False):
        (site_domain, app_domain) = entry.split('=')
        mappings[site_domain.strip()] = app_domain.strip()

    config.add_request_method(
        lambda request: mappings, name='group_mappings', reify=True)

    # tests will override the session, use the setting for everything else
    if isinstance(settings['app.db.url'], six.string_types):
        Session.configure(bind=sa.engine_from_config(settings, 'app.db.'))

    log.debug('Connected to: "%s"' % repr(Session.bind.url))


def groupfinder(identity, request):
    """
    Parse the groups from the identity into internal app groups
    """
    assert 'groups' in identity, \
        'Groups has not been set in the repoze identity!'
    mappings = request.group_mappings
    return [mappings[g] for g in identity['groups'] if g in mappings]


class RootFactory(object):

    __acl__ = [
        (Allow, Authenticated, 'view')
        ]

    def __init__(self, request):
        self.request = request


class AccountFactory(object):

    __acl__ = [
        (Allow, Authenticated, 'view')
        ]

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        try:
            user = Session.query(User).filter_by(key=key).one()
        except orm.exc.ResultNotFound:
            raise KeyError
        else:
            user.__parent__ = self
            user.__name__ = user.key
            return user


def _user_acl(self):
    return [
        (Allow, self.key, 'view'),  # Only allow the owner account
        ]

User.__acl__ = property(_user_acl)
