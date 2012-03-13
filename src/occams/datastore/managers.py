"""
DataStore data management utilitites
"""

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import object_session
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.scoping import ScopedSession
from zope.component import adapts
from zope.interface import implements
from zope.interface import classProvides

from occams.datastore.interfaces import IDataStore
from occams.datastore.interfaces import IHierarchy
from occams.datastore.interfaces import IDataStoreFactory
from occams.datastore.interfaces import ISchemaManager
from occams.datastore.interfaces import ISchemaManagerFactory
from occams.datastore.interfaces import ISchema
from occams.datastore.interfaces import IFieldManagerFactory
from occams.datastore.interfaces import IFieldManager
from occams.datastore.interfaces import IAttribute
from occams.datastore.interfaces import IValueManagerFactory
from occams.datastore.interfaces import IValueManager
from occams.datastore.interfaces import IValue
from occams.datastore.interfaces import IEntity
from occams.datastore.interfaces import IEntityManagerFactory
from occams.datastore.interfaces import IEntityManager
from occams.datastore import model


# Where the types are stored
#nameModelMap = dict(
#    integer=model.ValueInteger,
#    boolean=model.ValueInteger,
#    string=model.ValueString,
#    text=model.ValueString,
#    decimal=model.ValueDecimal,
#    date=model.ValueDatetime,
#    datetime=model.ValueDatetime,
#    object=model.ValueObject,
#    )
#
## What the types are cast to when queried
#nameSqlMap = dict(
#    integer=sqlalchemy.Integer,
#    string=sqlalchemy.Unicode,
#    text=sqlalchemy.UnicodeText,
#    boolean=sqlalchemy.Boolean,
#    decimal=sqlalchemy.Numeric,
#    date=sqlalchemy.Date,
#    datetime=sqlalchemy.DateTime,
#    object=sqlalchemy.Integer,
#    )
#
#valueModels = (
#    model.ValueDatetime,
#    model.ValueDecimal,
#    model.ValueInteger,
#    model.ValueObject,
#    model.ValueString
#    )


class DataStore(object):
    classProvides(IDataStoreFactory)
    implements(IDataStore)
    adapts(ScopedSession)

    def __init__(self, session):
        self.session = session
        self.storage = EntityManager(session)
        self.schemata = SchemaManager(session)

    @classmethod
    def create(cls, url):
        """ Convenience method for creating instances factory-style
        """
        engine = create_engine(url)
        session = scoped_session(sessionmaker(engine))
        instance = cls(session)
        return instance

    def __str__(self):
        class_ = self.__class__.__name__
        url = self.session.bind.url
        return u'<%(class_)s (\'%(bind)s\')>' % dict(class_=class_, bind=url)

    def spawn(self, *args, **kwargs):
        return ObjectFactory(*args, **kwargs)

    def keys(self, *args, **kwargs):
        return self.storage.keys(*args, **kwargs)

    def lifecycles(self, *args, **kwargs):
        return self.storage.lifecycles(*args, **kwargs)

    def has(self, *args, **kwargs):
        return self.storage.has(*args, **kwargs)

    def remove(self, *args, **kwargs):
        return self.storage.remove(*args, **kwargs)

    def retire(self, *args, **kwargs):
        return self.storage.retire(*args, **kwargs)

    def restore(self, *args, **kwargs):
        return self.storage.restore(*args, **kwargs)

    def get(self, *args, **kwargs):
        return self.storage.get(*args, **kwargs)

    def put(self, *args, **kwargs):
        return self.storage.put(*args, **kwargs)


class HierarchyInspector(object):
    implements(IHierarchy)
    adapts(ScopedSession)

    def __init__(self, session):
        self.session = session

    def getChildrenNames(self, key, on=None):
        return [schema.name for schema in self.getChildren(key, on)]

    def getChildrenNamesById(self, id):
        return [schema.name for schema in self.getChildrenById(id)]

    def getChildren(self , key, on=None):
        session = self.session
        query = session.query(model.Schema)
        if isinstance(key, basestring):
            query = query.filter_by(name=key)
        elif isinstance(key, int):
            query = query.filter_by(id=key)
        else:
            raise ValueError
        if on:
            query = query.filter(model.Schema.create_date >= on)
            query = query.order_by(model.Schema.create_date.asc())
        schema = query.first()
        if schema is None:
            raise KeyError
        return self.getChildrenOfSchema(schema)

    def getChildrenById(self, id):
        return self.getChildrenOfSchema(self.session(model.Schema).get(id))

    def getChildrenOfSchema(self, schema):
        result = []
        if schema is not None:
            for node in schema.sub_schemata:
                if node.sub_schemata:
                    children = self.getChildrenOfSchema(node)
                    result.extend(children)
                else:
                    result.append(node)
        return result


class SchemaManager(object):
    classProvides(ISchemaManagerFactory)
    implements(ISchemaManager)
    adapts(ScopedSession)

    def __init__(self, session):
        self.session = session

    def _query(self, key=None, on=None, ever=False):
        session = self.session
        query = session.query(model.Schema)
        if key is not None:
            query = query.filter_by(name=key)
        if on:
            query = query.filter(model.Schema.create_date >= on)
        if not ever:
            query = query.order_by(model.Schema.create_date.asc()).limit(1)
        return query

    def keys(self, on=None):
        query = self._query(on=on, ever=True).group_by('name')
        return [item.name for item in query.all()]

    def lifecycles(self, key):
        return [item.create_date for item in self._query(key=key, ever=True).all()]

    def has(self, key, on=None, ever=False):
        return self._query(key, on, ever).count() > 0

    def remove(self, key, on=None, ever=False):
        return self._query(key, on, ever).delete('fetch')

    def get(self, key, on=None):
        item = self._query(key, on).first()
        if item is None:
            raise KeyError('[\'%s\' as of \'%s\'] was not found' % (key, on))
        return item

    def getById(self, id):
        return self.session(model.Schema).get(id)

    def put(self, key, item):
        if not ISchema.providedBy(item):
            raise ValueError('%s does not provide %s' % (item, self.expects))

        if isinstance(key, basestring) and  key != item.name:
            raise ValueError('Key %s is not equal to item name %s' % (key, item.name))
        elif isinstance(key, int) and  key != item.id:
            raise ValueError('Key %s is not equal to item id %s' % (key, item.id))

        session = self.session
        session.add(item)
        session.flush()
        return item.id


class AttributeManager(object):
    classProvides(IFieldManagerFactory)
    implements(IFieldManager)
    adapts(ISchema)

    def __init__(self, schema):
        self.schema = schema
        self.session = object_session(schema)

    def _query(self, key=None, on=None, ever=False):
        session = self.session
        query = session.query(model.Attribute).filter_by(schema=self.schema)
        if key is not None:
            query = query.filter_by(name=key)
        if on:
            query = query.filter(model.Attribute.create_date >= on)
        if not ever:
            query = query.order_by(model.Attribute.create_date.asc()).limit(1)
        return query

    def keys(self, on=None):
        query = self._query(on=on, ever=True).group_by('name').order_by('order')
        return [item.name for item in query.all()]

    def lifecycles(self, key):
        return [item.create_date for item in self._query(key=key, ever=True).all()]

    def has(self, key, on=None, ever=False):
        return self._query(key, on, ever).count() > 0

    def remove(self, key, on=None, ever=False):
        return self._query(key, on, ever).delete('fetch')

    def get(self, key, on=None):
        session = self.session
        if isinstance(key, int):
            item = session.query(model.Attribute).get(key)
        else:
            item = self._query(key, on).first()
        if item is None:
            raise KeyError('[\'%s\' as of \'%s\'] was not found' % (key, on))
        return item

    def getById(self, id):
        return self.session.query(model.Attribute).get(id)

    def put(self, key, item):
        if not IAttribute.providedBy(item):
            raise ValueError('%s does not provide %s' % (item, self.expects))

        if isinstance(key, basestring) and  key != item.name:
            raise ValueError('Key %s is not equal to item name %s' % (key, item.name))
        elif isinstance(key, int) and  key != item.id:
            raise ValueError('Key %s is not equal to item id %s' % (key, item.id))

        session = self.session
        session.add(item)
        session.flush()
        return item.id


class EntityManager(object):
    classProvides(IEntityManagerFactory)
    implements(IEntityManager)
    adapts(ISchema)

    def __init__(self, schema):
        self.schema = schema
        self.session = object_session(schema)

    def _query(self, key=None, on=None, ever=False):
        session = self.session
        query = session.query(model.Entity).filter_by(schema=self.schema)
        if key is not None:
            query = query.filter_by(name=key)
        if on:
            query = query.filter(model.Entity.create_date >= on)
        if not ever:
            query = query.order_by(model.Entity.create_date.asc()).limit(1)
        return query

    def keys(self, on=None):
        query = self._query(on=on, ever=True).group_by('name').order_by('order')
        return [item.name for item in query.all()]

    def lifecycles(self, key):
        return [item.create_date for item in self._query(key=key, ever=True).all()]

    def has(self, key, on=None, ever=False):
        return self._query(key, on, ever).count() > 0

    def remove(self, key, on=None, ever=False):
        return self._query(key, on, ever).delete('fetch')

    def get(self, key, on=None):
        item = self._query(key, on).first()
        if item is None:
            raise KeyError('[\'%s\' as of \'%s\'] was not found' % (key, on))
        return item

    def getById(self, id):
        return self.session.query(model.Entity).get(id)

    def put(self, key, item):
        if not IEntity.providedBy(item):
            raise ValueError('%s does not provide %s' % (item, IEntity))

        if isinstance(key, basestring) and  key != item.name:
            raise ValueError('Key %s is not equal to item name %s' % (key, item.name))
        elif isinstance(key, int) and  key != item.id:
            raise ValueError('Key %s is not equal to item id %s' % (key, item.id))

        session = self.session
        session.add(item)
        session.flush()
        return item.id


class ValueManager(object):
    classProvides(IValueManagerFactory)
    implements(IValueManager)
    adapts(IEntity)

    def __init__(self, entity):
        self.session = object_session(entity)
        self.entity = entity

    def keys(self, on=None, ever=False):
        return [a.name for a in self.entity.schema.attributes]

    def lifecycles(self, key):
        return 1

    def has(self, key, on=None, ever=False):
        return key in self.entity.schema.attributes

    def remove(self, key, on=None, ever=False):
        session = self.session
        attribute = self.entity.schema.attributes[key]
        mapping = nameModelMap[attribute.type]
        query = session.query(mapping).filter_by(entity=self.entity, attribute=attribute)
        return query.delete('fetch')

    def get(self, key, on=None):
        session = self.session
        attribute = self.entity.schema.attributes[key]
        mapping = nameModelMap[attribute.type]
        query = session.query(mapping).filter_by(entity=self.entity, attribute=attribute)
        entries = query.all()
        if entries is None:
            raise KeyError('[\'%s\' as of \'%s\'] was not found' % (key, on))
        return entries if attribute.is_collection else entries[0]

    def getById(self, id):
        """ Can't do this for values, we don't know the value mapping ahead of time"""

    def put(self, key, item):
        session = self.session
        items = item if isinstance(item, list) else [item]

        for item in items:
            if not IValue.providedBy(item):
                raise ValueError('%s does not provide %s' % (item, IEntity))

        session.add_all(item)
