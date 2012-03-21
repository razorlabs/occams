"""
Responsible for the maintenance of Zope-style schemata that will be
then translated into an EAV structured database.
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
from occams.datastore.interfaces import typesVocabulary


class HierarchyInspector(object):
    implements(IHierarchy)
    adapts(ScopedSession)

    def __init__(self, session):
        self.session = session

    def getChildren(self , key, on=None):
        return [schemaToInterface(c) for c in self._children(self._get(key, on))]

    def getChildrenNames(self, key, on=None):
        return [c.name for c in self._children(self._get(key, on))]

    def _get(self, key, on=None):
        schema = model.Schema.asOf(key, on, self.session)
        if schema is None:
            raise ManagerKeyError(model.Schema, key, on)
        return schema

    def _children(self, schema):
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

    def __init__(self, session):
        self.session = session

    def _query(self, key=None, on=None, ever=False):
        session = self.session
        query = session.query(model.Schema).filter_by(state='published')
        # Filter schemata with the given name, if specified
        if key is not None:
            query = query.filter(model.Schema.name == unicode(key))
        # Filter schemata that exist as of the given date
        if on is not None:
            query = query.filter(model.Schema.publish_date <= on)
        # Ever is ignored now
        return query

    def keys(self, on=None, ever=False):
        return [i.name for i in self._query(on=on, ever=ever).group_by('name').all()]

    def lifecycles(self, key):
        return [i.publish_date for i in self._query(key=key).all()]

    def has(self, key, on=None, ever=False):
        return self._query(key=key, on=on, ever=ever).count() > 0

    def purge(self, key, on=None, ever=False):
        schema = model.Schema.asOf(key, on, self.session)
        if schema is not None:
            self.session.delete(schema)
            self.session.flush()
            return 1
        return 0

    def retire(self, key):
        raise NotImplementedError('Unsafe to purge series of Schema(%s)' % key)

    def restore(self, key):
        raise NotImplementedError('Cannot undo audit of Schema(%s)' % key)

    def get(self, key, on=None):
        schema = model.Schema.asOf(key, on, self.session)
        if schema is None:
            raise ManagerKeyError(model.Schema, key, on)
        return schemaToInterface(schema)

    def put(self, key, item):
        schema = interfaceToSchema(item)
        self.session.add(schema)
        self.session.flush()
        return schema.id


@adapter(ISchema)
@implementer(IInterface)
def schemaToInterface(schema):
    """
    Converts a schema to a zope interface
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
def attributeToField(session, attribute):
    """
    Converts an attribute to a zope schema field
    """

    factory = typesVocabulary.getTermByToken(attribute.type).value
    options = dict()

    if attribute.object_schema:
        options = dict(schema=schemaToInterface(attribute.object_schema))

    if attribute.choices:
        terms = []

        for choice in attribute.choices:
            (token, title, value) = (choice.name, choice.title, choice.value)
            terms.append(SimpleTerm(token=str(token), title=title, value=value))

        factory = zope.schema.Choice
        options = dict(vocabulary=SimpleVocabulary(terms))

    if attribute.is_collection:
        # Wrap the factory and options into the list
        options = dict(value_type=factory(**options), unique=True)
        factory = zope.schema.List

    # Update the options with the final field parameters
    options.update(dict(
        __name__=str(attribute.name),
        title=attribute.title,
        description=attribute.description,
        required=attribute.is_required,
        ))

    result = factory(**options)
    result.order = attribute.order

    if attribute.choices:
        directives.type.set(result, attribute.type)

    directives.__id__.set(result, attribute.id)
    directives.version.set(result, attribute.schema.publish_date)

    return result


@adapter(IInterface)
@implementer(ISchema)
def interfaceToSchema(iface):
    """
    Converts a zope interface into a **NEW** datastore schema
    This method ignores base interfaces because of the risk of potentially
    adding duplicate bases into the database.
    """

    if not directives.Schema.isEqualOrExtendedBy(iface):
        raise ValueError('%s is not a child class of %s' % (iface, directives.Schema))

    schema = model.Schema(
        name=iface.__class__.__name__,
        title=directives.title.bind().get(iface),
        description=directives.description.bind().get(iface),
        )

    for order, field in enumerate(zope.schema.getFieldsInOrder(iface), start=0):
        (name, field) = field
        schema.attributes[name] = fieldToAttribute(field)
        schema.attributes[name].order = order

    return schema


@adapter(IField)
@implementer(IAttribute)
def fieldToAttribute(field):
    """
    Converts a zope schema field into a **NEW** datastore attribute
    """
    properties = dict(
        name=field.__name__,
        title=field.title,
        description=field.description,
        is_collection=zope.schema.interfaces.ICollection.providedBy(field),
        is_required=field.required,
        choices=[],
        order=field.order,
        type=directives.type.bind().get(field)
        )

    field = field if not properties['is_collection'] else field.value_type

    if zope.schema.interfaces.IChoice.providedBy(field):
        try:
            validator = (typesVocabulary.getTermByToken(properties['type']).value)()
        except LookupError:
            raise ValueError

        for i, term in enumerate(field.vocabulary, start=0):
            validator.validate(term.value)
            properties['choices'].append(model.Choice(
                name=term.token,
                title=unicode(term.title is None and term.token or term.title),
                value=unicode(term.value),
                order=i,
                ))
    else:
        try:
            properties['type'] = typesVocabulary.getTerm(field.__class__).token
        except LookupError:
            raise ValueError

        if zope.schema.interfaces.IObject.providedBy(field):
            properties['object_schema'] = interfaceToSchema(field.schema)
            properties['object_schema'].is_inline = True

    return model.Attribute(**properties)
