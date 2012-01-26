"""
Various component browser traversal.

The traversal hierarchy goes as follows:

    - `repository/@@view`
    - `repository/formName`
    - `repository/formName/@@view`
    - `repository/formName/fieldName`
    - `repository/formName/fieldName/@@edit`
    - `repository/formName/fieldName/subFieldName`

Also, we'd like the following (not supported yet):

    - `repository/formName/entityName`
    - `repository/formName/entityName/@@view`

"""

from collective.beaker.interfaces import ISession
from OFS.SimpleItem import SimpleItem
from zope.component import adapts
from zope.component import queryMultiAdapter
from zope.container.interfaces import IReadContainer
from zope.interface import implements
from zope.publisher.defaultview import getDefaultViewName
from zope.publisher.interfaces.http import IHTTPRequest
from zope.publisher.interfaces.browser import IBrowserPublisher
from zExceptions import NotFound

from avrc.data.store import model
from avrc.data.store.interfaces import IDataStore
from occams.form.interfaces import DATA_KEY
from occams.form.interfaces import IRepository
from occams.form.interfaces import IDataBaseItemContext
from occams.form.interfaces import ISchemaContext
from occams.form.interfaces import IAttributeContext


class DataBaseItemContext(SimpleItem):
    """
    Wrapper context for database items to make them Zope-traversal-compatible
    """
    implements(IDataBaseItemContext)

    # The actual data we're wrapping
    item = None

    # Input data
    data = None

    def __init__(self, item=None, data=None):
        self.item = item
        self.data = data or dict()

        # Set the zope-expected properties
        self.id = None
        self.__name__ = str(self.data.get('name') or self.item.name)
        title = self.data.get('title') or self.item.name
        self.title = title
        self.Title = lambda: title

    def __getitem__(self, key):
        if key not in self:
            raise KeyError
        return self.data.get(key) or getattr(self.item, key)

    def __setitem__(self, key, value):
        if key not in self:
            raise KeyError
        self.data.set(key, value)
        if self.item is not None:
            setattr(self.item, key, value)

    def __contains__(self, key):
        return key in self.data or hasattr(self.item, key)


class SchemaContext(DataBaseItemContext):
    """
    Wrapper for schema (form) data
    """
    implements(ISchemaContext)


class AttributeContext(DataBaseItemContext):
    """
    Wrapper for attribute (field) data
    """
    implements(IAttributeContext)


class ExtendedTraversal(object):
    """
    Generic traverser for dynamic object URL traversal from non-zodb sources
    Parts of the code for this class adopted from ``grokcore.traverser``,
    except that the search order was changed to favor default machinery to
    avoid costly lookups.

    Expected usage is to extend this class as an adapter to the
    desired context/request pair.
    """

    implements(IBrowserPublisher)

    def __init__(self, context, request):
        """
        Convenience constructor so sub-classes don't have to set these values
        """
        self.context = context
        self.request = request

    def browserDefault(self, request):
        """
        Returns the default view name for the current context.
        Ideally, transient contexts should still register their default views
        with <browser:defaultView for="foo.context" name="view" />
        """
        view_name = getDefaultViewName(self.context, request)
        view_uri = "@@%s" % view_name
        return self.context, (view_uri,)

    def publishTraverse(self, request, name):
        """
        Traverses through the current context in the URL, favoring default
        machinery.
        """

        # Attempt traversal (the item is possibly in other sources)
        child = self.traverse(name)
        if child is not None:
            return child.__of__(self.context)

        # Attempt contained child lookup (for folder-ish types)
        if IReadContainer.providedBy(self.context):
            item = self.context.get(name)
            if item is not None:
                return item

        # Attempt view lookup (maybe the name is a view?)
        view = queryMultiAdapter((self.context, request), name=name)
        if view is not None:
            return view

        # Well screw it, we tried
        raise NotFound(self.context, name, request)

    def traverse(self, name):
        """
        Allows the ability to hook-in to zope's traversing machinery so that
        a context can be searched for in other sources besides the zodb
        """
        pass


class RepositoryTraverser(ExtendedTraversal):
    """
    Traverses through a ``IRepository`` to get an ``ISchemaContext``
    Note that from this point, we can only traverse to EXISTING forms. After
    that, we can traverse to form data (in case the form is being modified)
    """
    adapts(IRepository, IHTTPRequest)

    def traverse(self, name):
        workspace = ISession(self.request).get(DATA_KEY, {})

        if name in workspace:
            return SchemaContext(data=workspace[name])
        else:
            session = IDataStore(self.context).session

            query = (
                session.query(model.Schema)
                .filter(model.Schema.name == name)
                .filter(model.Schema.asOf(None))
                .order_by(model.Schema.name.asc())
                )

            item = query.first()

            if item is not None:
                return SchemaContext(item=item)


class SchemaTraverser(ExtendedTraversal):
    """
    Traverses through a ``ISchemContext`` to get an ``IAttributeContext``
    TODO Eventually we'll want to be able to traverse to an entity as well
    """
    adapts(ISchemaContext, IHTTPRequest)

    def traverse(self, name):
        if self.context.data:
            childData = self.context.data.get('fields', {}).get(name)
            if childData:
                return AttributeContext(data=childData)

class AttributeTraverser(ExtendedTraversal):
    """
    Traverses through an ``IAttributeContext`` to get ``IAttributeContext``
    values from sub-objects. This only works if the attribute that is
    being traversed is of type `object`.
    """
    adapts(IAttributeContext, IHTTPRequest)

    def traverse(self, name):
        if self.context.data:
            childData = self.context.data.get('schema', {}).get('fields', {}).get(name)
            if childData:
                return AttributeContext(data=childData)
