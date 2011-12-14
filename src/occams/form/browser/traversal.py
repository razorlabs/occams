"""
/fia-forms/@@view
/fia-forms/<formName>/@@view
/fia-forms/<formName>/<fieldName>/@@view

/fia-forms/<formName>/@@edit
/fia-forms/<formName>/<fieldName>/@@edit
/fia-forms/<formName>/<fieldName>/@@view
"""

from zope.component import adapts
from zope.component import queryMultiAdapter
from zope.interface import implements
from zope.publisher.interfaces.http import IHTTPRequest
from zope.publisher.interfaces.browser import IBrowserPublisher
from OFS.SimpleItem import SimpleItem
from zExceptions import NotFound

from collective.beaker.interfaces import ISession
from sqlalchemy.orm import object_session

from avrc.data.store import model
from avrc.data.store.interfaces import IDataStore

from occams.form.interfaces import SESSION_KEY
from occams.form.interfaces import IRepository
from occams.form.interfaces import IDataBaseItemContext
from occams.form.interfaces import ISchemaContext
from occams.form.interfaces import IEntityContext
from occams.form.interfaces import IAttributeContext


class DataBaseItemContext(SimpleItem):
    implements(IDataBaseItemContext)

    item = None

    def __init__(self, item):
        self.item = item
        self.id = None
        self.__name__ = item.name
        title = item.title
        self.Title = lambda: title


class SchemaContext(DataBaseItemContext):
    implements(ISchemaContext)


class AttributeContext(DataBaseItemContext):
    implements(IAttributeContext)


class EntityContext(DataBaseItemContext):
    implements(IEntityContext)


class RepositoryTraverse(object):
    """
    Traverses through a ``IRepository`` to get an ``ISchemaContext``
    """
    adapts(IRepository, IHTTPRequest)
    implements(IBrowserPublisher)

    def __init__(self, context, request):
        (self.context, self.request) = (context, request)

    def browserDefault(self, request):
        return self.context, ('@@view',)

    def publishTraverse(self, request, name):
        # Make sure we're not trying to go to one of the repository's actual views
        view = queryMultiAdapter((self.context, request), name=name)

        if view is not None:
            return view

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

        if item is None:
            browserSession = ISession(request)

            if SESSION_KEY in browserSession:
                for field in browserSession[SESSION_KEY]['fields'].values():
                    schemaData = field.get('schema')
                    if schemaData and schemaData['name'] == name:
                        item = model.Schema(
                            name=schemaData['name'],
                            title=schemaData['title']
                            )
                        break

        if item is not None:
            newContext = SchemaContext(item).__of__(self.context)
        else:
            raise NotFound()

        return newContext


class SchemaTraverse(object):
    """
    Traverses through a ``ISchemContext`` to get an 
    ``IAttributeContext`` or a ``IEntityContext``
    """
    adapts(ISchemaContext, IHTTPRequest)
    implements(IBrowserPublisher)

    def __init__(self, context, request):
        (self.context, self.request) = (context, request)

    def browserDefault(self, request):
        # Forms should just go to their edit forms, we don't have statistics
        # in place and maybe once that is complete we can go to that view
        # instead.
        return self.context, ('@@edit',)

    def publishTraverse(self, request, name):
        # Make sure we're not trying to go to one of the repository's actual views
        view = queryMultiAdapter((self.context, request), name=name)

        if view is not None:
            return view

        newContext = None

        # Try to find an attribute first
        item = self._findIn(model.Attribute, name)

        if item is not None:
            newContext = AttributeContext(item).__of__(self.context)
        else:
            # The attribute wasn't found, try to check if it's a data entry
            item = self._findIn(model.Entity, name)

            if item is not None:
                newContext = EntityContext(item).__of__(self.context)

        return newContext

    def _findIn(self, klass, name):
        schema = self.context.item
        session = object_session(schema)

        query = (
            session.query(klass)
            .filter(klass.schema.has(name=schema.name))
            .filter(klass.name == name)
            # TODO: this REALLY needs to work....
            .filter(klass.asOf(None))
            .order_by(klass.name.asc())
            )

        return query.first()


class AttributeTraverse(object):
    adapts(IAttributeContext, IHTTPRequest)
    implements(IBrowserPublisher)

    def __init__(self, context, request):
        (self.context, self.request) = (context, request)

    def browserDefault(self, request):
        # Forms should just go to their edit forms, we don't have statistics
        # in place and maybe once that is complete we can go to that view
        # instead.
        return self.context, ('@@edit',)

    def publishTraverse(self, request, name):
        return self.context

