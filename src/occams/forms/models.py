from pyramid.events import subscriber, NewRequest
from pyramid.security import Allow, Authenticated, ALL_PERMISSIONS
from pyramid.settings import aslist
import six
import sqlalchemy as sa
from sqlalchemy import orm

from occams.datastore.models import *  # NOQA

from . import log, Session


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

    log.debug('occams.forms connected to: "%s"' % repr(Session.bind.url))
    DataStoreModel.metadata.info['settings'] = settings


def groupfinder(identity, request):
    """
    Parse the groups from the identity into internal app groups
    """
    assert 'groups' in identity, \
        'Groups has not been set in the repoze identity!'
    mappings = request.group_mappings
    return [mappings[g] for g in identity['groups'] if g in mappings]


@subscriber(NewRequest)
def setup_request(event):
    request = event.request

    # Annotates the database session with the current user.
    Session.info['user'] = request.authenticated_userid

    # Store the CSRF token in a cookie since we'll need to sent it back
    # frequently in single-page views.
    # https://docs.djangoproject.com/en/dev/ref/contrib/csrf/
    # The attacker cannot read or change the value of the cookie due to the
    # same-origin policy, and thus cannot guess the right GET/POST parameter
    request.response.set_cookie('csrf_token', request.session.get_csrf_token())


class RootFactory(object):
    """
    Default root that enforces application permissions.

    Client applications with their own principles should define
    their own ``who.callback`` that maps client groups to application
    groups.
    """

    __acl__ = [(Allow, Authenticated, 'view')]

    def __init__(self, request):
        self.request = request


class FormFactory(object):

    __acl__ = [
        (Allow, 'administrator', ALL_PERMISSIONS),
        (Allow, 'manager', ('view', 'add')),
        (Allow, 'editor', ('view', 'add')),
        (Allow, Authenticated, 'view')]

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        (exists,) = (
            Session.query(
                Session.query(Schema)
                .filter_by(name=key)
                .exists())
            .one())
        if not exists:
            raise KeyError
        item = Form()
        item.__name__ = key
        item.__parent__ = self
        return item


class Form(object):

    __acl__ = [
        (Allow, Authenticated, 'view')
        ]

    def __getitem__(self, key):
        if key == 'versions':
            item = VersionFactory()
            item.__name__ = key
            item.__parent__ = self
            return item


class VersionFactory(object):

    __acl__ = [
        (Allow, 'administrator', ALL_PERMISSIONS),
        (Allow, 'manager', ('view', 'add')),
        (Allow, 'editor', ('view', 'add')),
        (Allow, Authenticated, 'view')]

    def __getitem__(self, key):
        query = (
            Session.query(Schema)
            .filter_by(name=self.__parent__.__name__))
        try:
            key = int(key)
        except ValueError:
            query = query.filter_by(publish_date=key)
        else:
            query = query.filter_by(id=key)

        try:
            schema = query.one()
        except orm.exc.NoResultFound:
            raise KeyError
        else:
            schema.__name__ = key
            schema.__parent__ = self
            return schema


def schema_acl(self):
    if not self.publish_date:
        return [
            (Allow, 'administrator', ALL_PERMISSIONS),
            (Allow, 'manager', ('view', 'edit', 'delete')),
            (Allow, 'editor', ('view', 'edit', 'delete')),
            (Allow, Authenticated, 'view')]
    else:
        return [
            (Allow, 'administrator', ALL_PERMISSIONS),
            (Allow, 'manager', ('view', 'edit', 'delete')),
            (Allow, 'editor', 'view')]


def schema_getitem(self, key):
    if key == 'fields':
        item = AttributeFactory()
        item.__name__ = key
        item.__parent__ = self
        return item


Schema.__acl__ = property(schema_acl)
Schema.__getitem__ = schema_getitem


class AttributeFactory(object):

    @property
    def __acl__(self):
        if not self.__parent__publish_date:
            return [
                (Allow, 'administrator', ALL_PERMISSIONS),
                (Allow, 'manager', ('view', 'edit', 'delete')),
                (Allow, 'editor', ('view', 'edit', 'delete'))]
        else:
            return [
                (Allow, 'administrator', ALL_PERMISSIONS),
                (Allow, 'manager', ('view', 'edit', 'delete')),
                (Allow, 'editor', 'view')]

    def __getitem__(self, key):
        try:
            attribute = (
                Session.query(Attribute)
                .filter_by(schema=self.__parent__, name=key)
                .one())
        except orm.exc.NoResultFound:
            raise KeyError
        else:
            attribute.__name__ = key
            attribute.__parent__ = self
            return attribute


def attribute_acl(self):
    if not self.__parent__.publish_date:
        return [
            (Allow, 'administrator', ALL_PERMISSIONS),
            (Allow, 'manager', ('view', 'edit', 'delete')),
            (Allow, 'editor', ('view', 'edit', 'delete')),
            (Allow, Authenticated, 'view')]
    else:
        return [
            (Allow, 'administrator', ALL_PERMISSIONS),
            (Allow, 'manager', ('view', 'edit', 'delete')),
            (Allow, 'editor', 'view')]


Attribute.__acl__ = property(attribute_acl)
