"""
Schema utilities
"""

from sqlalchemy.orm.scoping import ScopedSession
from zope.component import adapts
from zope.component import adapter
from zope.interface import classProvides
from zope.interface import implements
from zope.interface import implementer
from zope.interface.interface import InterfaceClass
from zope.interface.interfaces import IInterface
import zope.schema
from zope.schema.interfaces import IField
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

from occams.datastore import model
from occams.datastore import directives
from occams.datastore.interfaces import ManagerKeyError
from occams.datastore.interfaces import IHierarchy
from occams.datastore.interfaces import ISchema
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

    def getChildren(self , key, on=None):
        return [schemaToInterface(c) for c in self._children(self._get(key, on))]

    getChildren.__doc__ = IHierarchy['getChildren'].__doc__

    def getChildrenNames(self, key, on=None):
        return [c.name for c in self._children(self._get(key, on))]

    getChildrenNames.__doc__ = IHierarchy['getChildrenNames'].__doc__

    def _get(self, key, on=None):
        """
        Helper method to fetch a schema instance from the database

        Arguments
            ``key``
                The name of the schema to fetch
            ``on``
                The date reference for the publication
        """
        session = self.session
        query = session.query(model.Schema).filter_by(name=key, state='published')
        if on:
            query = query.filter(model.Schema.publish_date <= on)
        query = query.order_by(model.Schema.publish_date.desc())
        schema = query.first()
        if schema is None:
            raise ManagerKeyError(model.Schema, key, on)
        return schema

    def _children(self, schema):
        """
        Helper method to return all the children (leaf nodes in the hierarchy)
        of a schema.

        Arguments
            ``schema``
                The schema model instance to traverse
        Returns
            A list of the leaf nodes of the current schema
        """
        result = []
        for node in schema.sub_schemata:
            if node.sub_schemata:
                result.extend(self._children(node))
            else:
                result.append(node)
        return result


class SchemaManager(object):
    classProvides(ISchemaManagerFactory)
    implements(ISchemaManager)
    adapts(ScopedSession)

    __doc__ = ISchemaManager.__doc__

    def __init__(self, session):
        self.session = session

    __init__.__doc__ = ISchemaManagerFactory['__call__'].__doc__

    def keys(self, on=None, ever=False):
        query = self.session.query(model.Schema)
        if on:
            query = query.filter(model.Schema.publish_date <= on)
        else:
            query = query.filter(model.Schema.publish_date != None)
        query = query.group_by('name')
        return [i.name for i in query.all()]

    keys.__doc__ = ISchemaManager['keys'].__doc__

    def lifecycles(self, key):
        query = self.session.query(model.Schema).filter_by(name=key)
        query = query.filter(model.Schema.publish_date != None)
        query = query.order_by(model.Schema.publish_date.desc())
        return [i.publish_date for i in query.all()]

    lifecycles.__doc__ = ISchemaManager['lifecycles'].__doc__

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
            query = query.order_by(model.Schema.publish_date.desc())
            schema = query.first()
            if schema is not None:
                session.delete(schema)
                return 1
            else:
                return 0
        else:
            return query.delete('fetch')

    purge.__doc__ = ISchemaManager['purge'].__doc__

    def retire(self, key):
        raise NotImplementedError('Unsafe to purge series of Schema(%s)' % key)

    retire.__doc__ = ISchemaManager['retire'].__doc__

    def restore(self, key):
        raise NotImplementedError('Cannot undo audit of Schema(%s)' % key)

    restore.__doc__ = ISchemaManager['restore'].__doc__

    def get(self, key, on=None):
        session = self.session
        query = session.query(model.Schema).filter_by(name=key)
        if on:
            query = query.filter(model.Schema.publish_date <= on)
        else:
            query = query.filter(model.Schema.publish_date != None)
        query = query.order_by(model.Schema.publish_date.desc())
        schema = query.first()
        if schema is None:
            raise ManagerKeyError(model.Schema, key, on)
        return schemaToInterface(schema)

    get.__doc__ = ISchemaManager['get'].__doc__

    def put(self, key, item):
        session = self.session
        id = directives.__id__.bind().get(item)
        if id:
            # Raise an error that about existing schemata. Note, though,
            # that user can be savvy and remove the id, in which case then
            # the database will bark an Integrity Error
            raise ValueError('Cannot modify existing published schemata')
        if not directives.version.bind().get(item):
            raise ValueError('Cannot put a schema missing a publication date')
        schema = interfaceToSchema(item)
        if schema.base_schema is not None:
            # If the incoming schema has a base class, try to reuse an existing one
            base_schema = (
                session.query(model.Schema)
                .filter_by(name=schema.base_schema.name)
                .filter(model.Schema.publish_date != None)
                .order_by(model.Schema.publish_date.desc())
                .first()
                )
            if base_schema is not None:
                schema.base_schema = base_schema
        session.add(schema)
        session.flush()
        directives.__id__.set(item, schema.id)
        return schema.id

    put.__doc__ = ISchemaManager['put'].__doc__


def copy(schema):
    """
    Copies a schema's properties into a new instance of a schema

    Arguments
        ``schema``
            A SQLAlchemy schema instance to be copied
    Returns
        A new instance containing 'most' of the properties of the old schema,
        with exception of data such as metadata and state/publication
        information
    """
    schemaList = (
        'base_schema', 'name', 'title', 'description', 'storage', 'is_inline',
        )
    attributeList = (
        'name', 'title', 'description', 'type', 'is_collection',
        'object_schema', 'object_schema_id',
        'is_required', 'collection_min', 'collection_max',
        'value_min', 'value_max', 'validator', 'order'
        )
    choiceList = ('name', 'title', 'description', 'value', 'order')

    createFrom = lambda c, l: c.__class__(**dict([(p, getattr(c, p)) for p in l]))

    schemaCopy = createFrom(schema, schemaList)

    for attributeName, attribute in schema.attributes.items():
        attributeCopy = createFrom(attribute, attributeList)
        schemaCopy.attributes[attributeName] = attributeCopy

        if attribute.type == 'object':
            attributeCopy.object_schema = copy(attribute.object_schema)

        for choice in attribute.choices:
            attributeCopy.choices.append(createFrom(choice, choiceList))

    return schemaCopy


@adapter(ISchema)
@implementer(IInterface)
def schemaToInterface(schema):
    """
    Converts a SQLAlchemy schema instance into a Zope-style instance
    """

    if schema.base_schema:
        ibase = schemaToInterface(schema.base_schema)
    else:
        ibase = directives.Schema

    iface = InterfaceClass(
        name=str(schema.name),
        bases=[ibase],
        attrs=dict([(a.name, attributeToField(a)) for a in iter(schema.attributes)]),
        )

    directives.__id__.set(iface, schema.id)
    directives.title.set(iface, schema.title)
    directives.description.set(iface, schema.description)
    directives.version.set(iface, schema.publish_date)

    return iface


@adapter(IAttribute)
@implementer(IField)
def attributeToField(attribute):
    """
    Converts a SQLAlchemy attribute instance into a Zope-style field
    """

    # Start off with the basic raw factory for the type
    factory = typesVocabulary.getTermByToken(attribute.type).value

    # Build the parameters needed as the attribute is processed
    options = dict()

    if attribute.object_schema:
        options = dict(schema=schemaToInterface(attribute.object_schema))

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

    # Configure the directives for better hinting
    directives.__id__.set(result, attribute.id)
    directives.type.set(result, attribute.type)
    directives.version.set(result, attribute.schema.publish_date)

    return result


@adapter(IInterface)
@implementer(ISchema)
def interfaceToSchema(iface):
    """
    Converts a Zope-style interface into a SQLAlchemy schema instance

    Raises
        ``ValueError``
            This exception is raised when the incoming interface does not
            properly subclass the ``directves.Schema`` marker -OR- it
            contains multiple base classes.
    """

    if not directives.Schema.isEqualOrExtendedBy(iface):
        raise ValueError('%s is not a child class of %s' % (iface, directives.Schema))

    if len(iface.__bases__) > 1:
        raise ValueError('%s has more than one base (Not supported)' % iface)
    elif len(iface.__bases__) == 1 and iface.__bases__[0] != directives.Schema:
        base_schema = interfaceToSchema(iface.__bases__[0])
    else:
        base_schema = None

    schema = model.Schema(
        base_schema=base_schema,
        name=iface.__name__,
        title=directives.title.bind().get(iface),
        description=directives.description.bind().get(iface),
        publish_date=directives.version.bind().get(iface),
        )

    if schema.publish_date:
        schema.state = 'published'

    for order, field in enumerate(zope.schema.getFieldsInOrder(iface), start=0):
        (name, field) = field
        schema.attributes[name] = fieldToAttribute(field)
        schema.attributes[name].order = order

    return schema


@adapter(IField)
@implementer(IAttribute)
def fieldToAttribute(field):
    """
    Converts a Zope-style filed into a SQLAlchemy attribute instance
    """

    properties = dict(
        name=field.__name__,
        title=field.title,
        description=field.description,
        is_collection=zope.schema.interfaces.ICollection.providedBy(field),
        is_required=field.required,
        choices=[],
        order=field.order,
        )

    properties['type'] = directives.type.bind().get(field)

    if properties['type'] is None:
        typeField = getattr(field, 'value_type', field)
        if not zope.schema.interfaces.IChoice.providedBy(typeField):
            properties['type'] = typesVocabulary.getTerm(typeField.__class__).token
        else:
            raise ValueError('Received field with choices and  with no type directive')
    else:
        typeField = field

    if zope.schema.interfaces.IChoice.providedBy(typeField):
        validator = (typesVocabulary.getTermByToken(properties['type']).value)()

        for i, term in enumerate(typeField.vocabulary, start=0):
            validator.validate(term.value)
            properties['choices'].append(model.Choice(
                name=term.token,
                title=unicode(term.title is None and term.token or term.title),
                value=unicode(term.value),
                order=i,
                ))
    else:
        properties['type'] = typesVocabulary.getTerm(typeField.__class__).token

        if zope.schema.interfaces.IObject.providedBy(typeField):
            properties['object_schema'] = interfaceToSchema(typeField.schema)
            properties['object_schema'].is_inline = True

    return model.Attribute(**properties)
