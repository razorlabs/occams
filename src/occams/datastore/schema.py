"""
Schema utilities
"""

from sqlalchemy.orm.scoping import ScopedSession
from sqlalchemy.orm.exc import NoResultFound
from zope.component import adapts
from zope.component import adapter
from zope.interface import classProvides
from zope.interface import implements
from zope.interface import implementer
import zope.schema
from zope.schema.interfaces import IField
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

from occams.datastore import model
from occams.datastore.interfaces import NotFoundError
from occams.datastore.interfaces import IHierarchy
from occams.datastore.interfaces import IAttribute
from occams.datastore.interfaces import ISchemaManager
from occams.datastore.interfaces import ISchemaManagerFactory
from occams.datastore.interfaces import IHierarchyFactory
from occams.datastore.interfaces import typesVocabulary


class HierarchyInspector(object):
    classProvides(IHierarchyFactory)
    implements(IHierarchy)
    adapts(ScopedSession)

    __doc__ = IHierarchy.__doc__

    def __init__(self, session):
        self.session = session

    __init__.__doc__ = IHierarchyFactory['__call__'].__doc__

    def children(self , key, on=None):
        return list(self.iterChildren(key, on))

    children.__doc__ = IHierarchy['children'].__doc__

    def iterChildren(self, key, on=None):
        def children(schema):
            """ Helper method to iterate through childre"""
            # Iterate through the children
            for child in iter(schema.sub_schemata):
                # If the child has children as well, continue recursion
                if child.sub_schemata:
                    for leaf in children(child):
                        yield leaf
                # Otherwise return the child as a leaf
                else:
                    yield child

        return children(SchemaManager(self.session).get(key, on))

    iterChildren.__doc__ = IHierarchy['iterChildren'].__doc__

    def childrenNames(self, key, on=None):
        return list(self.iterChildrenNames(key, on))

    childrenNames.__doc__ = IHierarchy['childrenNames'].__doc__

    def iterChildrenNames(self, key, on=None):
        for child in self.iterChildren(key, on):
            yield child.name

    iterChildrenNames.__doc__ = IHierarchy['iterChildrenNames'].__doc__


class SchemaManager(object):
    classProvides(ISchemaManagerFactory)
    implements(ISchemaManager)
    adapts(ScopedSession)

    __doc__ = ISchemaManager.__doc__

    def __init__(self, session):
        self.session = session

    __init__.__doc__ = ISchemaManagerFactory['__call__'].__doc__

    def keys(self, on=None, ever=False):
        query = self.session.query(model.Schema.name)
        if on:
            query = query.filter(model.Schema.publish_date <= on)
        else:
            query = query.filter(model.Schema.publish_date != None)
        query = query.group_by('name')
        return [i.name for i in iter(query)]

    keys.__doc__ = ISchemaManager['keys'].__doc__

    def has(self, key, on=None, ever=False):
        query = self.session.query(model.Schema).filter_by(name=key)
        if on:
            query = query.filter(model.Schema.publish_date <= on)
        else:
            query = query.filter(model.Schema.publish_date != None)
        return query.count() > 0

    has.__doc__ = ISchemaManager['has'].__doc__

    def purge(self, key, on=None, ever=False):
        session = self.session
        query = session.query(model.Schema).filter_by(name=key)
        if on:
            query = query.filter(model.Schema.publish_date <= on)
        else:
            query = query.filter(model.Schema.publish_date != None)
        if not ever:
            query = query.order_by(model.Schema.publish_date.desc()).limit(1)
            try:
                schema = query.one()
            except NoResultFound:
                return 0
            else:
                session.delete(schema)
                return 1
        else:
            return query.delete('fetch')

    purge.__doc__ = ISchemaManager['purge'].__doc__

    def get(self, key, on=None):
        session = self.session
        query = session.query(model.Schema).filter_by(name=key)
        if on:
            query = query.filter(model.Schema.publish_date <= on)
        else:
            query = query.filter(model.Schema.publish_date != None)
        query = query.order_by(model.Schema.publish_date.desc())
        query = query.limit(1)
        try:
            schema = query.one()
        except NoResultFound:
            raise NotFoundError(model.Schema, (key, on))
        else:
            return schema

    get.__doc__ = ISchemaManager['get'].__doc__

    def put(self, key, item):
        session = self.session
        if item.name is None and key is None:
            raise ValueError
        elif item.name is None:
            item.name = key
        session.add(item)
        session.flush()
        return item.id

    put.__doc__ = ISchemaManager['put'].__doc__


@adapter(IAttribute)
@implementer(IField)
def attributeToField(attribute):
    """
    Converts a SQLAlchemy attribute instance into a Zope-style field
    """

    if attribute.type == 'object':
        raise ValueError('Cannot convert objects to fields: %s' % attribute)

    # Start off with the basic raw factory for the type
    factory = typesVocabulary.getTermByToken(attribute.type).value

    # Build the parameters needed as the attribute is processed
    options = dict()

    # If dealing with answer choices, configure the factory
    if attribute.choices:
        terms = []

        # Build the Zope-style vocabulary
        for choice in attribute.choices:
            (token, title, value) = (choice.name, choice.title, choice.value)
            terms.append(SimpleTerm(token=str(token), title=title, value=value))

        factory = zope.schema.Choice
        options = dict(vocabulary=SimpleVocabulary(terms))

    # If dealing with collections of values, configure the factory
    if attribute.is_collection:
        # Wrap the factory and original options into the list
        options = dict(value_type=factory(**options), unique=True)
        factory = zope.schema.List

    # Update the options with the final field parameters
    options.update(dict(
        __name__=str(attribute.name),
        title=attribute.title,
        description=attribute.description,
        required=bool(attribute.is_required),
        ))

    result = factory(**options)

    # Order can't be one of the parameters, so assign it separately
    result.order = attribute.order

    return result

