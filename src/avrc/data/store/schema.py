"""
Responsible for the maintenance of Zope-style schemata that will be
then translated into an EAV structured database.
"""

from zope.component import adapts
from zope.interface import classProvides
from zope.interface import alsoProvides
from zope.interface import implements
from zope.interface.interface import InterfaceClass
import zope.schema
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.vocabulary import SimpleTerm

from sqlalchemy.orm import object_session
from sqlalchemy.orm.scoping import ScopedSession

from avrc.data.store import directives
from avrc.data.store import model
from avrc.data.store.interfaces import typesVocabulary
from avrc.data.store.interfaces import ISchemaFormat
from avrc.data.store.interfaces import IHierarchy
from avrc.data.store.interfaces import ISchema
from avrc.data.store.interfaces import ISchemaManager
from avrc.data.store.interfaces import IFieldManager
from avrc.data.store.interfaces import ISchemaManagerFactory
from avrc.data.store.interfaces import IFieldManagerFactory
from avrc.data.store.interfaces import NotCompatibleError
from avrc.data.store.interfaces import MultipleBasesError
from avrc.data.store.interfaces import TypeNotSupportedError
from avrc.data.store.interfaces import ChoiceTypeNotSpecifiedError


class HierarchyInspector(object):
    implements(IHierarchy)
    adapts(ScopedSession)


    def __init__(self, session):
        self.session = session


    def getChildren(self , key, on=None):
        session = self.session
        query = (
            session.query(model.Schema)
            .filter_by(name=key)
            .filter(model.Schema.asOf(on))
            )
        schema = query.first()
        entries = self._getChildrenOfSchema(schema)
        manager = SchemaManager(session)
        result = [manager.get(entry.name, on) for entry in entries]
        return result


    def getChildrenNames(self, key, on=None):
        session = self.session
        query = (
            session.query(model.Schema)
            .filter_by(name=key)
            .filter(model.Schema.asOf(on))
            )
        schema = query.first()
        entries = self._getChildrenOfSchema(schema)
        result = [(entry.name, entry.title) for entry in entries]
        return result


    def _getChildrenOfSchema(self, schema):
        result = []
        if schema is not None:
            for node in schema.sub_schemata:
                if node.sub_schemata:
                    children = self._getChildrenOfSchema(node)
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


    def keys(self, on=None, ever=False):
        session = self.session
        query = session.query(model.Schema.name)
        if not ever:
            query = query.filter(model.Schema.asOf(on))
        result = [key for (key,) in query.all()]
        return result


    def lifecycles(self, key):
        session = self.session
        query = (
            session.query(model.Schema.create_date.label('event_date'))
            .union(
                session.query(model.Schema.remove_date),
                session.query(model.Attribute.create_date),
                session.query(model.Attribute.remove_date)
                )
            .order_by('event_date ASC')
            )
        result = [event_date for (event_date,) in query.all()]
        return result


    def has(self, key, on=None, ever=False):
        session = self.session
        query = session.query(model.Schema).filter_by(name=key)
        if not ever:
            query = query.filter(model.Schema.asOf(on))
        result = query.count()
        return result


    def purge(self, key, on=None, ever=False):
        session = self.session
        query = session.query(model.Schema).filter_by(name=key)
        if not ever:
            query = query.filter(model.Schema.asOf(on))
        result = query.delete('fetch')
        return  result


    def retire(self, key):
        session = self.session
        query = (
            session.query(model.Schema)
            .filter_by(name=key)
            .filter(model.Schema.asOf(None))
            )
        result = query.update(dict(remove_date=model.NOW), 'fetch')
        return result


    def restore(self, key):
        session = self.session
        query = (
            session.query(model.Schema)
            .filter(None != model.Schema.remove_date)
            .filter(model.Schema.id == (
                session.query(model.Schema.id)
                .filter(key == model.Schema.name)
                .order_by(
                    model.Schema.create_date.desc()
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
            session.query(model.Schema)
            .filter(key == model.Schema.name)
            .filter(model.Schema.asOf(on))
            )
        schema = query.first()
        iface = None

        if schema is not None:
            # Process the base classes first
            if schema.base_schema:
                ibase = self.get(schema.base_schema.name, on=on)
            else:
                ibase = directives.Schema

            # Call Field manager
            manager = FieldManager(schema)
            attribute_keys = manager.keys(on=on)
            attributes = dict()

            for attribute_name in attribute_keys:
                field = manager.get(attribute_name, on=on)
                attributes[str(attribute_name)] = field

            iface = InterfaceClass(
                name=str(schema.name),
                bases=[ibase],
                attrs=attributes,
                )

            alsoProvides(iface, ISchemaFormat)

            directives.__id__.set(iface, schema.id)
            directives.title.set(iface, schema.title)
            directives.description.set(iface, schema.description)
            directives.version.set(iface, schema.create_date)

        return iface


    def put(self, key, item):
        """
        Note: If no key assigned (None), one will be generated
        """
        if not directives.Schema.isEqualOrExtendedBy(item):
            raise NotCompatibleError

        if key != item.__name__:
            raise Exception

        session = self.session

        self.retire(key)

        if 1 < len(item.__bases__):
            raise MultipleBasesError
        elif 1 == len(item.__bases__) and directives.Schema != item.__bases__[0]:
            # Actually, since we're adding to the top of the stack, we should
            # techinally just be getting the most recent version of the
            # base schema.
            query = (
                session.query(model.Schema)
                .filter(item.__bases__[0].__name__ == model.Schema.name)
                .filter(model.Schema.asOf(None))
                )
            base_schema = query.first()
        else:
            base_schema = None

        schema = model.Schema(base_schema=base_schema, name=key)
        session.add(schema)

        schema.title = directives.title.bind().get(item)
        schema.description = directives.description.bind().get(item)
        session.flush()

        directives.__id__.set(item, schema.id)
        directives.version.set(item, schema.create_date)

        manager = FieldManager(schema)
        for name, field in zope.schema.getFieldsInOrder(item):
            manager.put(name, field)

        return schema.id


class FieldManager(object):
    classProvides(IFieldManagerFactory)
    implements(IFieldManager)
    adapts(ISchema)


    def __init__(self, schema):
        self.session = object_session(schema)
        self.schema = schema




    def keys(self, on=None, ever=False):
        session = self.session
        query = (
            session.query(model.Attribute.name)
            .filter(model.Attribute.schema.has(name=self.schema.name))
            .order_by(model.Attribute.order.asc(), model.Attribute.create_date.asc())
            )
        if not ever:
            query = query.filter(model.Attribute.asOf(on))
        result = [key for (key,) in query.all()]
        return result


    def lifecycles(self, key):
        session = self.session
        query = (
            session.query(model.Attribute.create_date.label('event_date'))
            .filter(model.Attribute.schema.has(name=self.schema.name))
            .filter_by(name=key)
            .union(
                session.query(model.Attribute.remove_date)
                .filter_by(schema=self.schema, name=key)
                )
            .order_by('event_date ASC')
            )
        result = [event_date for (event_date,) in query.all()]
        return result


    def has(self, key, on=None, ever=False):
        session = self.session
        query = (
            session.query(model.Attribute)
            .filter(model.Attribute.schema.has(name=self.schema.name))
            .filter_by(name=key)
            )
        if not ever:
            query = query.filter(model.Attribute.asOf(on))
        result = query.count()
        return result


    def purge(self, key, on=None, ever=False):
        session = self.session
        query = (
            session.query(model.Attribute)
            .filter(model.Attribute.schema.has(name=self.schema.name))
            .filter_by(name=key)
            )
        if not ever:
            query = query.filter(model.Attribute.asOf(on))
        result = query.delete('fetch')
        return  result


    def retire(self, key):
        if self.schema.remove_date is not None:
            raise Exception('Cannot retire a schema field that has been retired.')
        session = self.session
        query = (
            session.query(model.Attribute)
            .filter(model.Attribute.schema.has(name=self.schema.name))
            .filter_by(name=key)
            .filter(model.Attribute.asOf(None))
            )
        result = query.update(dict(remove_date=model.NOW), 'fetch')
        return result


    def restore(self, key):
        session = self.session
        query = (
            session.query(model.Attribute)
            .filter(None != model.Attribute.remove_date)
            .filter(model.Attribute.id == (
                session.query(model.Attribute.id)
                .filter(model.Attribute.schema.has(name=self.schema.name))
                .filter_by(name=key)
                .order_by(
                    model.Attribute.create_date.desc()
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
            session.query(model.Attribute)
            .filter(model.Attribute.schema.has(name=self.schema.name))
            .filter_by(name=key)
            .filter(model.Attribute.asOf(on))
            )
        attribute = query.first()
        result = None

        if attribute:
            factory = typesVocabulary.getTermByToken(attribute.type).value
            options = dict()

            if attribute.object_schema:
                manager = SchemaManager(session)
                schema = manager.get(attribute.object_schema.name, on=on)
                factory = zope.schema.Object
                options = dict(schema=schema)

            if attribute.choices:
                terms = []
                validator = factory(**options)
                query = (
                    session.query(model.Choice)
                    .filter_by(attribute=attribute)
                    .order_by(model.Choice.order.asc())
                    )

                for choice in query.all():
                    (token, title, value) = (choice.name, choice.title, choice.value)
                    term = SimpleTerm(token=str(token), title=title, value=value)
                    terms.append(term)
                factory = zope.schema.Choice
                options = dict(vocabulary=SimpleVocabulary(terms))

            if attribute.is_collection:
                # Wrap the factory and options into the list
                options = dict(value_type=factory(**options), unique=True)
                factory = zope.schema.List

            if attribute.default:
                options['default'] = factory(**options).fromUnicode(attribute.default)
            # Update the options with the final field parameters
            options.update(dict(
                __name__=str(attribute.name),
                title=attribute.title,
                description=attribute.description,
                readonly=attribute.is_readonly,
                required=attribute.is_required,
                ))

            result = factory(**options)
            result.order = attribute.order

            if attribute.choices:
                directives.type.set(result, attribute.type)
            directives.__id__.set(result, attribute.id)
            directives.version.set(result, attribute.create_date)

        return result


    def put(self, key, item):
        if self.schema.remove_date is not None:
            raise Exception('Cannot modify a schema field that has been retired.')
        session = self.session
        is_collection = zope.schema.interfaces.ICollection.providedBy(item)
        field = item if not is_collection else item.value_type
        choices = dict()
        object_schema = None

        self.retire(field.__name__)

        if zope.schema.interfaces.IChoice.providedBy(field):
            type = directives.type.bind().get(item)
            try:
                validator = (typesVocabulary.getTermByToken(type).value)()
            except LookupError:
                raise ChoiceTypeNotSpecifiedError

            for i, term in enumerate(field.vocabulary, start=1):
                (name, title, value) = (term.token, term.title, term.value)
                validator.validate(value)
                title = title is None and name or title
                title = unicode(title)
                name = str(name)
                value = unicode(value)
                choice = model.Choice(name=name, title=title, value=value, order=i)
                choices[choice.name] = choice
        else:
            try:
                type = typesVocabulary.getTerm(field.__class__).token
            except LookupError:
                raise TypeNotSupportedError

            if zope.schema.interfaces.IObject.providedBy(field):
                iface = field.schema
                object_schema_id = directives.__id__.bind().get(iface)
                object_schema = session.query(model.Schema).get(object_schema_id)

        attribute = model.Attribute(
            schema=self.schema,
            name=item.__name__,
            title=item.title,
            description=item.description,
            type=type,
            choices=choices,
            object_schema=object_schema,
            is_inline_object=directives.inline.bind().get(field),
            is_readonly=item.readonly,
            is_collection=is_collection,
            is_required=item.required,
            default=(unicode(item.default) if item.default is not None else None),
            order=item.order
            )

        session.add(attribute)
        session.flush()

        directives.__id__.set(item, attribute.id)
        directives.version.set(item, attribute.create_date)

        return attribute.id
