from pyramid.security import Allow, Authenticated, ALL_PERMISSIONS
from sqlalchemy import orm

from occams_datastore import models as datastore


class FormFactory(object):

    __acl__ = [
        (Allow, 'administrator', ALL_PERMISSIONS),
        (Allow, 'manager', ('view', 'add')),
        (Allow, 'editor', ('view', 'add')),
        (Allow, Authenticated, 'view')]

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        db_session = self.request.db_session
        (exists,) = (
            db_session.query(
                db_session.query(datastore.Schema)
                .filter_by(name=key)
                .exists())
            .one())
        if not exists:
            raise KeyError
        item = Form(self.request)
        item.__name__ = key
        item.__parent__ = self
        return item


class Form(object):

    __acl__ = [
        (Allow, Authenticated, 'view')
        ]

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        if key == 'versions':
            item = VersionFactory(self.request)
            item.__name__ = key
            item.__parent__ = self
            return item


class VersionFactory(object):

    __acl__ = [
        (Allow, 'administrator', ALL_PERMISSIONS),
        (Allow, 'manager', ('view', 'add')),
        (Allow, 'editor', ('view', 'add')),
        (Allow, Authenticated, 'view')]

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        db_session = self.request.db_session
        query = (
            db_session.query(datastore.Schema)
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
            (Allow, 'manager', ('view', 'edit', 'delete', 'draft')),
            (Allow, 'editor', ('view', 'draft'))]


def schema_getitem(self, key):
    db_session = orm.object_session(self)
    request = db_session.info['request']
    if key == 'fields':
        item = AttributeFactory(request)
        item.__name__ = key
        item.__parent__ = self
        return item


datastore.Schema.__acl__ = property(schema_acl)
datastore.Schema.__getitem__ = schema_getitem


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

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        db_session = self.request.db_session
        try:
            attribute = (
                db_session.query(datastore.Attribute)
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


datastore.Attribute.__acl__ = property(attribute_acl)
