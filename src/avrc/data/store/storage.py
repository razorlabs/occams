""" Schema-based data entry utilities.
"""

from datetime import date
from datetime import datetime

from zope.component import adapts
from zope.interface import Interface
from zope.interface import implements
from zope.interface import providedBy
from zope.interface import classProvides
from zope.interface import directlyProvides
import zope.schema

import sqlalchemy
from sqlalchemy.orm import object_session
from sqlalchemy.orm.scoping import ScopedSession

from avrc.data.store import directives
from avrc.data.store import model as dsmodel
from avrc.data.store.interfaces import IInstance
from avrc.data.store.interfaces import IEntity
from avrc.data.store.interfaces import IEntityManager
from avrc.data.store.interfaces import IValueManager
from avrc.data.store.interfaces import IEntityManagerFactory
from avrc.data.store.interfaces import IValueManagerFactory
from avrc.data.store.interfaces import PropertyNotDefinedError
from avrc.data.store.interfaces import InvalidObjectError
from avrc.data.store.schema import SchemaManager


# Where the types are stored
nameModelMap = dict(
    integer=dsmodel.ValueInteger,
    boolean=dsmodel.ValueInteger,
    string=dsmodel.ValueString,
    text=dsmodel.ValueString,
    decimal=dsmodel.ValueDecimal,
    date=dsmodel.ValueDatetime,
    datetime=dsmodel.ValueDatetime,
    object=dsmodel.ValueObject,
    )

# What the types are cast to when queried
nameSqlMap = dict(
    integer=sqlalchemy.Integer,
    string=sqlalchemy.Unicode,
    text=sqlalchemy.UnicodeText,
    boolean=sqlalchemy.Boolean,
    decimal=sqlalchemy.Numeric,
    date=sqlalchemy.Date,
    datetime=sqlalchemy.DateTime,
    object=sqlalchemy.Integer,
    )

valueModels = (
    dsmodel.ValueDatetime,
    dsmodel.ValueDecimal,
    dsmodel.ValueInteger,
    dsmodel.ValueObject,
    dsmodel.ValueString
    )


class Item(object):
    """ 
    Base class for objects with an interface.
    """

    def __init__(self, **kwargs):
        """ 
        Constructor method that uses the schema's fields as key word arguments.
        """
        try:
            schema = list(providedBy(self))[0]
        except KeyError:
            raise Exception('No interface found')

        for name in schema.names():
            if name in kwargs:
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
    if not iface.extends(Interface):
        raise Exception('%s will not be found' % iface)

    class Instance(object):
        implements(IInstance)

        # TODO (mmartinez): support these as directives somehow
        __id__ = None
        __schema__ = None
        __state__ = None
        __name__ = None
        __title__ = None
        __version__ = None

        def setState(self, state):
            self.__state__ = unicode(state)

        def getState(self):
            return self.__state__

        def __eq__(self, other):
            return self.__id__ == getattr(other, '__id__', None)

    result = Instance()
    directlyProvides(result, iface)

    result.__schema__ = iface

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


    def keys(self, on=None, ever=False):
        session = self.session
        query = session.query(dsmodel.Entity.name)
        if not ever:
            query = query.filter(dsmodel.Entity.asOf(on))
        result = [key for (key,) in query.all()]
        return result


    def lifecycles(self, key):
        session = self.session
        query = (
            session.query(dsmodel.Entity.create_date.label('event_date'))
            .union(
                session.query(dsmodel.Entity.remove_date),
                session.query(dsmodel.Assignment.create_date),
                session.query(dsmodel.Assignment.remove_date),
                )
            .order_by('event_date ASC')
            )
        result = [event_date for (event_date,) in query.all()]
        return result


    def has(self, key, on=None, ever=False):
        session = self.session
        query = session.query(dsmodel.Entity).filter_by(name=key)
        if not ever:
            query = query.filter(dsmodel.Entity.asOf(on))
        result = query.count()
        return result


    def purge(self, key, on=None, ever=False):
        session = self.session
        query = session.query(dsmodel.Entity).filter_by(name=key)
        if not ever:
            query = query.filter(dsmodel.Entity.asOf(on))
        result = query.delete('fetch')
        return  result


    def retire(self, key):
        session = self.session
        query = (
            session.query(dsmodel.Entity)
            .filter_by(name=key)
            .filter(dsmodel.Entity.asOf(None))
            )
        result = query.update(dict(remove_date=dsmodel.NOW), 'fetch')
        return result


    def restore(self, key):
        session = self.session
        query = (
            session.query(dsmodel.Entity)
            .filter(None != dsmodel.Entity.remove_date)
            .filter(dsmodel.Entity.id == (
                session.query(dsmodel.Entity.id)
                .filter_by(name=key)
                .order_by(
                    dsmodel.Entity.create_date.desc()
                    )
                .limit(1)
                .as_scalar()
                ))
            )
        result = query.update(dict(remove_date=None), 'fetch')
        return result


    def get(self, key, on=None):
        session = self.session
        query = (
            session.query(dsmodel.Entity)
            .filter_by(name=key)
            .filter(dsmodel.Entity.asOf(on))
            )
        entity = query.first()

        if entity is not None:
            manager = ValueManager(entity)
            values = dict([(n, manager.get(n, on=on)) for n in manager.keys(on=on)])
            iface = SchemaManager(session).get(entity.schema.name, on=entity.create_date)
            result = ObjectFactory(iface, **values)
            result.__dict__.update(dict(
                __id__=entity.id,
                __name__=entity.name,
                __title__=entity.title,
                __schema__=iface,
                __state__=(entity.state and entity.state.name or None),
                __version__=entity.create_date,
                ))
        else:
            result = None

        return result


    def _inspectState(self, item):
        session = self.session
        state = item.getState()
        filter = state is None and dict(is_default=True) or dict(name=state)
        state = session.query(dsmodel.State).filter_by(**filter).first()
        return state


    def put(self, key, item):
        if not IInstance.providedBy(item):
            raise InvalidObjectError

        session = self.session
        name = u''
        title = u''
        is_new = True

        state = item.getState()
        filter = state is None and dict(is_default=True) or dict(name=state)
        state = session.query(dsmodel.State).filter_by(**filter).first()

        iface = item.__schema__
        schema_id = directives.__id__.bind().get(iface)
        schema_name = iface.__name__
        schema_title = directives.title.bind().get(iface)

        if item.__name__ is not None:
            name = item.__name__
            title = item.__title__
            is_new = False
            self.retire(name)

        entity = dsmodel.Entity(schema_id=schema_id, name=name, title=title, state=state)
        session.add(entity)
        session.flush()

        if is_new:
            entity.name = '%s-%d' % (schema_name, entity.id)
            entity.title = u'%s-%d' % (schema_title, entity.id)
            session.flush()

        item.__id__ = entity.id
        item.__name__ = entity.name
        item.__title__ = entity.title
        item.__schema__ = iface
        item.__state__ = entity.state and entity.state.name or None
        item.__version__ = entity.create_date

        value_manager = ValueManager(entity)

        for field_name, field in zope.schema.getFieldsInOrder(iface):
            value = getattr(item, field_name, None)
            value_manager.put(field_name, value)

        return item.__id__


class ValueManager(object):
    classProvides(IValueManagerFactory)
    implements(IValueManager)
    adapts(IEntity)


    def __init__(self, entity):
        self.session = object_session(entity)
        self.entity = entity

        if entity.remove_date is not None:
            raise Exception('Cannot modify an entity that has already been retired.')


    def keys(self, on=None, ever=False):
        session = self.session
        query = (
            session.query(dsmodel.Assignment)
            .filter_by(entity=self.entity)
            )
        if not ever:
            query = query.filter(dsmodel.Assignment.asOf(on))
        result = [entry.attribute.name for entry in query.all()]
        return result


    def lifecycles(self, key):
        session = self.session
        query = (
            session.query(dsmodel.Assignment.create_date.label('event_date'))
            .filter_by(entity=self.entity)
            .filter(dsmodel.Assignment.attribute.has(name=key))
            .union(
                session.query(dsmodel.Assignment.remove_date)
                .filter_by(entity=self.entity)
                .filter(dsmodel.Assignment.attribute.has(name=key))
                )
            .order_by('event_date ASC')
            )
        result = [event_date for (event_date,) in query.all()]
        return result


    def has(self, key, on=None, ever=False):
        session = self.session
        query = (
            session.query(dsmodel.Assignment)
            .filter_by(entity=self.entity)
            )
        query = query.filter(dsmodel.Assignment.attribute.has(name=key))
        if not ever:
            query = query.filter(dsmodel.Assignment.asOf(on))
        result = query.count()
        return result



    def purge(self, key, on=None, ever=False):
        session = self.session
        result = 0
        query = (
            session.query(dsmodel.Assignment)
            .filter_by(entity=self.entity)
            .filter(dsmodel.Assignment.attribute.has(name=key))
            )
        if not ever:
            query = query.filter(dsmodel.Assignment.asOf(on))
        assignment = query.first()
        if assignment is not None:
            attribute = assignment.attribute
            type = attribute.type
            value_dsmodel = nameModelMap[type]
            query = (
                session.query(value_dsmodel)
                .filter_by(entity=self.entity)
                .filter_by(attribute=attribute)
                )
            if not ever:
                query = query.filter(value_dsmodel.asOf(on))
            result = query.delete('fetch')
        return result


    def retire(self, key):
        session = self.session
        result = 0
        query = (
            session.query(dsmodel.Assignment)
            .filter_by(entity=self.entity)
            .filter(dsmodel.Assignment.attribute.has(name=key))
            .filter(dsmodel.Assignment.asOf(None))
            )
        assignment = query.first()
        if assignment is not None:
            attribute = assignment.attribute
            type = attribute.type
            value_dsmodel = nameModelMap[type]
            query = (
                session.query(value_dsmodel)
                .filter_by(entity=self.entity)
                .filter_by(attribute=attribute)
                .filter(value_dsmodel.asOf(None))
                )
            result = query.update(dict(remove_date=dsmodel.NOW), 'fetch')
        return result


    def restore(self, key):
        session = self.session
        result = 0
        query = (
            session.query(dsmodel.Assignment)
            .filter_by(entity=self.entity)
            .filter(dsmodel.Assignment.attribute.has(name=key))
            .order_by('remove_date DESC NULLS FIRST')
            )
        assignment = query.first()
        if assignment is not None and assignment.remove_date is not None:
            attribute = assignment.attribute
            type = attribute.type
            value_dsmodel = nameModelMap[type]
            # This particular query matches by removal date, as there can be
            # many of the same removal date (lists)
            query = (
                session.query(value_dsmodel)
                .filter_by(entity=self.entity)
                .filter_by(attribute=attribute)
                .filter(assignment.remove_date == value_dsmodel.remove_date)
                )
            result = query.update(dict(remove_date=None), 'fetch')
        return result


    def get(self, key, on=None):
        session = self.session
        result = None
        query = (
            session.query(dsmodel.Assignment)
            .filter_by(entity=self.entity)
            .filter(dsmodel.Assignment.attribute.has(name=key))
            .filter(dsmodel.Assignment.asOf(on))
            )
        assignment = query.first()
        if assignment is not None:
            result = list()
            value_dsmodel = nameModelMap[assignment.attribute.type]
            query = (
                session.query(value_dsmodel)
                .filter_by(entity=self.entity)
                .filter_by(attribute=assignment.attribute)
                .filter(value_dsmodel.asOf(on))
                )
            entries = query.all()
            for entry in entries:
                # Special types need some extra processing
                if 'object' == assignment.attribute.type:
                    manager = EntityManager(session)
                    value = manager.get(entry.value_object.name, on=on)
                elif 'boolean' == assignment.attribute.type:
                    value = bool(entry.value)
                elif 'date' == assignment.attribute.type:
                    value = entry.value.date()
                else:
                    value = entry.value
                result.append(value)
            if not assignment.attribute.is_collection:
                result = result[0]
        return result


    def put(self, key, item):
        session = self.session
        item = item if isinstance(item, list) else [item]
        result = None
        entries = []
        entity = self.entity

        if isinstance(key, basestring):
            query = (
                session.query(dsmodel.Attribute)
                .filter_by(name=key, schema=entity.schema)
                .filter(dsmodel.Attribute.asOf(None))
                )
            attribute = query.first()
        else:
            attribute_id = directives.__id__.bind().get(key)
            attribute = entity.schema.attributes.get(attribute_id)

        if attribute is None:
            raise PropertyNotDefinedError

        value_dsmodel = nameModelMap[attribute.type]

        query = (
            session.query(value_dsmodel)
            .filter_by(entity=entity, attribute=attribute, remove_date=None)
            )

        # RETIRE values not in the item and ignore existing values
        for entry in query.all():
            if item:
                if entry.value not in item:
                    entry.remove_date = dsmodel.NOW
                else:
                    item.remove(entry.value)

        for value in item:
            if value is not None:
                # Find the choice it came from before the value is converted
                query = (
                    session.query(dsmodel.Choice)
                    .filter_by(attribute=attribute, value=unicode(value))
                    )
                choice = query.first()
                if 'object' == attribute.type:
                    entity_manager = EntityManager(session)
                    value = entity_manager.put(getattr(value, '__name__', None), value)
                elif 'boolean' == attribute.type:
                    value = int(value)
                entry = value_dsmodel(
                    entity=entity,
                    attribute=attribute,
                    choice=choice,
                    value=value
                    )
                entries.append(entry)

        if entries:
            session.add_all(entries)
            session.flush()
            result = [entry.id for entry in entries]
            if not attribute.is_collection and len(result):
                result = result[0]

        return result
