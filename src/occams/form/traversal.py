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
try:
    from repoze.zope2.publishtraverse import DefaultPublishTraverse
except ImportError:
    from ZPublisher.BaseRequest import DefaultPublishTraverse
from OFS.SimpleItem import SimpleItem
from zope.component import adapts
from zope.interface import implements
from zope.publisher.interfaces.http import IHTTPRequest
from zope.publisher.interfaces.browser import IBrowserPublisher
from zExceptions import NotFound
from z3c.saconfig import named_scoped_session
from occams.datastore import model
from occams.form.interfaces import IRepository
from occams.form.interfaces import IDataBaseItemContext
from occams.form.interfaces import ISchemaContext
from occams.form.interfaces import IAttributeContext
from occams.form.serialize import Workspace


def closest(context, iparent):
    """
    Utility method for finding the closest parent context with the given
    interface. Search begins at the specified context.
    """
    result = None
    while context is not None:
        if iparent.providedBy(context):
            result = context
            break
        else:
            context = context.getParentNode()
    return result


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
        title = self.data.get('title') or self.item.title
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


class ExtendedTraversal(DefaultPublishTraverse):
    """
    Generic traverser for dynamic object URL traversal from non-zodb sources
    Parts of the code for this class adopted from ``grokcore.traverser``,
    except that the search order was changed to favor default machinery to
    avoid costly lookups.

    Expected usage is to extend this class as an adapter to the
    desired context/request pair.
    """

    implements(IBrowserPublisher)

    def publishTraverse(self, request, name):
        """
        Traverses through the current context in the URL, favoring default
        machinery.
        """
        # Attempt traversal (the item is possibly in other sources)
        child = self.traverse(name)
        if child is not None:
            return child.__of__(self.context)

        # Well screw it, we tried
        return super(ExtendedTraversal, self).publishTraverse(request, name)

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
        import pdb; pdb.set_trace( )
        model.Schema.id.label('id'),
        workspace = Workspace(self.context)
        try:
            formData = workspace[name]
        except KeyError:
            session = named_scoped_session(self.context.session)
            item = (
                session.query(model.Schema)
                .filter(model.Schema.name == name)
                .order_by(model.Schema.publish_date.desc()
                .limit(1)).one()
                )
            context = item and SchemaContext(item=item) or None
        else:
            context = SchemaContext(data=formData)
        return context


class SchemaTraverser(ExtendedTraversal):
    """
    Traverses through a ``ISchemContext`` to get an ``IAttributeContext``
    TODO Eventually we'll want to be able to traverse to an entity as well
    """
    adapts(ISchemaContext, IHTTPRequest)

    def traverse(self, name):
        if name == 'view' and self.context.data is None:
            raise NotFound()
        try:
            if self.context.data:
                childData = self.context.data['fields'][name]
        except KeyError:
            context = None
        else:
            context = AttributeContext(data=childData)
        return context


class AttributeTraverser(ExtendedTraversal):
    """
    Traverses through an ``IAttributeContext`` to get ``IAttributeContext``
    values from sub-objects. This only works if the attribute that is
    being traversed is of type `object`.
    """
    adapts(IAttributeContext, IHTTPRequest)

    def traverse(self, name):
        try:
            if self.context.data:
                childData = self.context.data['schema']['fields'][name]
        except KeyError:
            context = None
        else:
            context = AttributeContext(data=childData)
        return context
