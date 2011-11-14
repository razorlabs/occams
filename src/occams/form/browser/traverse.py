from five import grok
from grokcore.component.interfaces import IContext
from grokcore.traverser import Traverser

from sqlalchemy.orm import object_session

from avrc.data.store import model
from avrc.data.store.interfaces import IDataStore
from avrc.data.store.interfaces import ISchema
from avrc.data.store.interfaces import IAttribute
from avrc.data.store.interfaces import IEntity


from occams.form import Logger as log
from occams.form.interfaces import IRepository
from occams.form.interfaces import IDataBaseItemContext
from occams.form.interfaces import ISchemaContext
from occams.form.interfaces import IEntityContext
from occams.form.interfaces import IAttributeContext


class DataBaseItemContext(grok.Model):
    grok.implements(IDataBaseItemContext)

    _item = None

    def __init__(self, item):
        super(DataBaseItemContext, self).__init__(item.name)
        self._item = item
        self.title = item.title

    @property
    def item(self):
        return self._item


class SchemaContext(DataBaseItemContext):
    grok.implements(ISchemaContext)


class AttributeContext(DataBaseItemContext):
    grok.implements(IAttributeContext)


class EntityContext(DataBaseItemContext):
    grok.implements(IEntityContext)


@grok.adapter(ISchema)
@grok.implementer(IContext)
def schemaContextFactory(item):
    return SchemaContext(item)


@grok.adapter(IAttribute)
@grok.implementer(IContext)
def attributeContextFactory(item):
    return AttributeContext(item)


@grok.adapter(IEntity)
@grok.implementer(IContext)
def entityContextFactory(item):
    return EntityContext(item)


class RepositoryTraverse(Traverser):
    """
    Traverses through a ``IRepository`` to get an ``ISchemaContext``
    """
    grok.context(IRepository)

    def traverse(self, name):
        if '-' in name or name in self.context:
            return

        datastore = IDataStore(self.context)
        session = datastore.session
        newContext = None

        query = (
            session.query(model.Schema)
            .filter(model.Schema.name == name)
            .filter(model.Schema.asOf(None))
            .order_by(model.Schema.name.asc())
            )

        item = query.first()

        if item is not None:
            log.info('Traversing from \'%s\' to \'%s\'' % (self.context.id, item.name))
            newContext = IContext(item).__of__(self.context)

        return newContext


class SchemaTraverse(Traverser):
    """
    Traverses through a ``IRepository`` to get an 
    ``ISchemaContext`` or a ``IEntityContext``
    """
    grok.context(ISchemaContext)

    def traverse(self, name):
        if '-' in name or name in self.context:
            return

        schema = self.context.item
        session = object_session(schema)
        newContext = None

        # Try to find an attribute first

        query = (
            session.query(model.Attribute)
            .filter(model.Attribute.schema.has(name=schema.name))
            .filter(model.Attribute.name == name)
            .filter(model.Attribute.asOf(schema.create_date))
            .order_by(model.Attribute.name.asc())
            )

        item = query.first()

        if item is None:
            # The attribute wasn't found, try to check if it's a data entry
            query = (
                session.query(model.Entity)
                .filter(model.Entity.schema.has(name=schema.name))
                .filter(model.Entity.name == name)
                .filter(model.Entity.asOf(schema.create_date))
                .order_by(model.Entity.name.asc())
                )

            item = query.first()

        if item is not None:
            log.info('Traversing from \'%s\' to \'%s\'' % (self.context.item.name, item.name))
            newContext = IContext(item).__of__(self.context)

        return newContext
