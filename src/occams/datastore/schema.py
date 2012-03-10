"""
Responsible for the maintenance of Zope-style schemata that will be
then translated into an EAV structured database.
"""

from zope.component import adapts
from zope.interface import classProvides
from zope.interface import implements
import zope.schema
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.vocabulary import SimpleTerm

from sqlalchemy.orm import object_session
from sqlalchemy.orm.scoping import ScopedSession

from occams.datastore import directives
from occams.datastore import model
from occams.datastore.interfaces import typesVocabulary
from occams.datastore.interfaces import IHierarchy
from occams.datastore.interfaces import ISchema
from occams.datastore.interfaces import ISchemaManager
from occams.datastore.interfaces import IFieldManager
from occams.datastore.interfaces import ISchemaManagerFactory
from occams.datastore.interfaces import IFieldManagerFactory


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

    def _query(self, key=None, on=None, ever=False):
        session = self.session
        query = session.query(model.Schema)
        if key is not None:
            if isinstance(key, basestring):
                query = query.filter_by(name=key)
            elif isinstance(key, int):
                query = query.filter_by(id=key)
            else:
                raise TypeError('%s of type %s is unsupported' % (key, type(key)))
        if on:
            query = query.filter(model.Schema.create_date >= on)
        if not ever:
            query = query.order_by(model.Schema.create_date.asc()).limit(1)
        return query

    def keys(self, on=None):
        query = self._query(on=on, ever=True).group_by(model.Schema.name)
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
            schema = session.query(model.Schema).get(key)
        else:
            schema = self._query(key, on).first()
        if schema is None:
            raise KeyError('[\'%s\' as of \'%s\'] was not found' % (key, on))
        return schema

    def put(self, key, item):
        if not ISchema.providedBy(item):
            raise ValueError('%s does not provide %s' % (item, ISchema))

        if isinstance(key, basestring) and  key != item.name:
            raise ValueError('Key %s is not equal to item name %s' % (key, item.name))
        elif isinstance(key, int) and  key != item.id:
            raise ValueError('Key %s is not equal to item id %s' % (key, item.id))

        session = self.session
        session.add(item)
        session.flush()
        return item.id


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

            for i, term in enumerate(field.vocabulary, start=0):
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

        if attribute.description is not None:
            attribute.description = attribute.description.strip() or None

        session.add(attribute)
        session.flush()

        directives.__id__.set(item, attribute.id)
        directives.version.set(item, attribute.create_date)

        return attribute.id
