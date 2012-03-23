""" Schema-based data entry utilities.
"""

from sqlalchemy.orm.scoping import ScopedSession
from zope.component import adapts
from zope.interface import implements
from zope.interface import providedBy
from zope.interface import classProvides
from zope.interface import directlyProvides
from zope.interface import alsoProvides
import zope.schema
from zope.schema.interfaces import IObject

from occams.datastore import model
from occams.datastore import directives
from occams.datastore.schema import schemaToInterface
from occams.datastore.interfaces import IInstance
from occams.datastore.interfaces import IEntityManager
from occams.datastore.interfaces import IEntityManagerFactory


class Item(object):
    """
    Base class for objects with an interface.
    """

    def __init__(self, **kwargs):
        """
        Constructor method that uses the schema's fields as key word arguments.
        """
        try:
            # If this object indeed has an interface we'll use it to
            # constraint the parameters
            iface = list(providedBy(self))[0]
        except KeyError:
            # Just a regular object
            pass
        else:
            for name in iface.names():
                setattr(self, name, kwargs.get(name))


def ObjectFactory(iface, **kwargs):
    """
    Spawns 'anonymous' objects from interface specifications.

    Arguments
        ``iface``
            A Zope-style Interface
        ``kwargs``:
            Values to apply to the newly created object
    """
    result = type('Instance', [Item])()
    alsoProvides(result, IInstance)
    directlyProvides(result, iface)

    result.__dict__.extend(dict(
        # TODO (mmartinez): support these as directives somehow
        __id__=None,
        __name__=None,
        __title__=None,
        __version__=None,
        __schema__=iface,
        __state__=None,
        __collect_date__=None,
        __entity__=None,
        setState=lambda self, state: setattr(self, '__state__', unicode(state),
        getstate=lambda self: self.__state__,
        setCollectionDate=lambda self, date: setattr(self, '__collection_date__', date),
        getCollectionDate=lambda self: self.__collection_date__,
        __eq__=lambda self, other: self.__id__ == getattr(other, '__id__', None),
        )))

    for field_name, field in zope.schema.getFieldsInOrder(iface):
        # TODO: figure out how to use FieldProperty with this
        subkwargs = kwargs.get(field_name)
        if isinstance(field, zope.schema.Object) and subkwargs is not None:
            ## This is a subobject, and should be generated
            if IInstance.providedBy(subkwargs):
                ## hey now, I'm already an Instance object
                value = subkwargs
            else:
                value = ObjectFactory(field.schema, **subkwargs)
        else:
            value = kwargs.get(field_name)
        result.__dict__[field_name] = value

    return result


class EntityManager(object):
    classProvides(IEntityManagerFactory)
    implements(IEntityManager)
    adapts(ScopedSession)

    def __init__(self, session):
        self.session = session
        self.query = (
            session.query(model.Entity)
            .filter(model.Entity.schema.has(state='published'))
            .filter(model.Entity.state.in_(['complete', 'not-done']))
            )

    def keys(self, on=None, ever=False):
        return [entity.name for entity in self.query.group_by('name').all()]

    def lifecycles(self, key):
        entity = self.query.filter_by(name=key).all()
        if entity:
            if len(entity) > 1:
                raise Exception
            return [entity.collect_date]

    def has(self, key, on=None, ever=False):
        return self.query.filter(name=key).count() > 0

    def purge(self, key, on=None, ever=False):
        result = self.query.filter(name=key).delete('fetch')
        self.session.flush()
        return result

    def retire(self, key):
        return self.purge(key)

    def restore(self, key):
        raise NotImplementedError

    def get(self, key, on=None):
        entity = self.query.filter_by(name=key).first()
        if entity is None:
            raise KeyError

        # Get the zope style schema
        iface = schemaToInterface(entity.schema)

        # Generate the bare values for each entity property
        values = dict()

        for name, value in entity.items():
            if entity.schema[name].type == 'object':
                raw = self.get(value.value.name)
            else:
                raw = value.value
            values[name] = raw

        # Create the object and assigne the hints
        result = ObjectFactory(iface, **values)
        result.__dict__.update(dict(
            __id__=entity.id,
            __name__=entity.name,
            __title__=entity.title,
            __schema__=iface,
            __entity__=entity,
            __state__=(entity.state and entity.state.name or None),
            __version__=entity.create_date,
            __collect_date=entity.collect_date,
            ))

        return result

    def put(self, key, item):
        entity = self.session.query(model.Entity).get(item.__id__)
        if entity is None:
            entity = model.Entity()

        for field_name, field in zope.schema.getFieldsInOrder(item.__schema__):
            value = getattr(item, field_name, None)
            if IObject.providedBy(field):
                value_id = self.put(None, value)
                value = self.session.query(model.Entity).get(value_id)
            entity[field_name] = value

        entity.name = item.__name__
        entity.title = item.__title__
        entity.schema_id = directives.__id__.bind().get(item.__schema__)
        entity.state = item.__state__

        self.session.add(entity)
        self.session.flush()

        item.__id__ = entity.id
        item.__name__ = entity.name
        item.__title__ = entity.title
        item.__state__ = entity.state and entity.state.name or None
        item.__version__ = entity.create_date
        item.__collect_date__ = entity.collect_date

        return entity.id

