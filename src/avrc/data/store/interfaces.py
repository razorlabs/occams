"""
Exposes specification for the components that will make up the data store
package.

Note that not all of the functionality will currently be in place, but this
is a good area to specify all the components that would be nice to have in
the long term.
"""

from zope.app.container.interfaces import IContained
from zope.interface import Interface
from zope.interface import  Attribute
from zope.i18nmessageid import MessageFactory
import zope.schema

_ = MessageFactory(__name__)

# -----------------------------------------------------------------------------
# ERRORS
# -----------------------------------------------------------------------------

class Error(Exception):
    """Base class for all errors in this package"""

class DatatoreError(Error):
    """Base class for data store-related errors"""

class SchemaError(Error):
    """Base class for schema-related errors"""

class UndefinedSchemaError(Error):
    """Raised when trying to access a schema that is not in the data store"""

# -----------------------------------------------------------------------------
# API CONTRACTS
# -----------------------------------------------------------------------------

class IComponent(Interface):
    """
    Base interface for the components of this package.
    """

class IManager(IComponent):
    """
    Specification for management components, that is, components that are in
    charge of a particular class of data. Note that a manager is simply a
    utility into to the data store, therefore creating multiple instances
    of a manager should have no effect on the objects being managed as they
    are still being pulled from the same source.
    """

    def keys():
        """
        Generates a collection of the keys for the objects the component is
        managing.

        Returns:
            A listing of the object keys being managed by this manager.
        """

    def has(key):
        """
        Checks if the component is managing the item.

        Arguments:
            key: an item that can be used to find the component in the manager.

        Returns:
            True if the manager is in control of the item.
        """

    def get(key):
        """
        Arguments:
            key: an item that can be used to find the component in the manager.
        Returns:
            An object maintained by the manger. None if not found.
        """

    def purge(key):
        """
        Completely removes the target and all data associated with it from the
        data store.

        Arguments:
            key: an item that can be used to find the component in the manager.
        Returns:
            N\A
        """

    def retire(key):
        """
        Expire's the contained target. This means that it's information remains,
        only it's not visible anymore. The reason this functionality is useful
        is so that data can be 'brought back' if expiring caused undesired
        side-effects.

        Arguments:
            key: an item that can be used to find the component in the manager.
        Returns:
            N\A
        """

    def put(target):
        """
        Adds or modifies the target into the manager

        Arguments:
            target: an object that will be added to this component's manager.
        Returns:
            N\A
        """

class ISchemaManager(IManager):
    """
    Marker interface for managing schemata.
    """

class IDomainManager(IManager):
    """
    Marker interface for managing domains
    """

class IDatastore(IManager, IContained):
    """
    Represents a data store utility that can be added to a site. It is in
    charge of managing the entire network of data that will be created from
    schemata, etc.
    """

    title = zope.schema.TextLine(
        title=_(u"Title"),
        description=_(u"A human readable title for this data store."),
        )

    dsn = zope.schema.URI(
        title=_(u"Data Source Name"),
        description=_(u"URL to the location of database to use for physical "
                       "storage.")
        )

class IMutableSchema(IComponent):
    """
    This is used when the schemata are going to be modified.
    """

class ISessionFactory(IComponent, IContained):
    """
    Used for implementing our own SQLAlchemy session. The reason for using our
    own Interface instead of a third party's such as z3c.saconfig is because
    we need more control over our sesession (e.g. need multiple engines
    per Session as opposed to the single engine allowed by z3c.saconfig"
    """

    def __call__():
        """
        Returns the generated SQLAlchemy Session
        """

class IInstance(IComponent):
    """
    """

    __schema__ = Attribute(_(u"The specific schema this is an instance of "
                             u"including the medata/version/etc"
                             ))

    __id__ = Attribute(_(u""))

class IKey(IComponent):
    """
    """

    __key__ = Attribute(_(u"A way to distinguish this item in the data store"))

class IVersionable(IComponent):
    """
    """

    __version__ = Attribute(_(u"This will be used to keep track of the "
                              u"data store schema as they evolve"))

class IFormable(IComponent):
    """
    Represents a schema that contains detailed information for display in a
    form.
    """

    __title__ = Attribute(_(u"A way to represent the name of in the form"))

    __description__ = Attribute(_(u"A way to represent the description."))

    __dependants__ = Attribute(_(u"Dependant schemata"))

class ISchema(IVersionable, IFormable):
    """
    Huzzah
    """

class IRange(IComponent, zope.schema.interfaces.ITuple):

    low = zope.schema.Int(title=u"The low")

    high = zope.schema.Int(title=u"The high")

class IReportable(IComponent):
    """
    Interface for generatged schema Promises to do some form of reporting
    """

    def report():
        """
        """

class IQueryLine(IComponent):
    """
    """
    value = zope.schema.TextLine(
        title=_(u"Search"),
        )

class IQuery(IComponent):
    """
    Querying contract.
    STILL IN PLANNING STAGES
    """

    contains = zope.schema.List(
        title=_(u"Phrases"),
        description=_(u"Contains any of the listed terms."),
        value_type=zope.schema.TextLine(title=_(u"Phrase")),
        required=False,
        )

    some = zope.schema.List(
        title=_(u"Some Phrases"),
        description=_("Contains one or more of the listed terms."),
        min_length=1,
        max_length=3,
        value_type=zope.schema.TextLine(title=_(u"Phrase")),
        required=False,
        )

    ignore = zope.schema.List(
        title=_(u"Do not include"),
        description=_(u"Do not include the listed terms."),
        value_type=zope.schema.TextLine(title=_(u"Phrase")),
        required=False,
        )

    domain = zope.schema.List(
        title=_(u"Domain search"),
        description=_(u"Search within a domain only."),
        value_type=zope.schema.TextLine(title=_(u"Phrase")),
        required=False,
        )

    date = zope.schema.Choice(
        title=_(u"Date"),
        description=_(u"How recent is the entry?"),
        values=(_(u"anytime"),
                _(u"past 24 hours"),
                _(u"past week"),
                _(u"past month"),
                _(u"past year")),
        required=False
        )

    range = zope.schema.List(
        title=_(u"Numeric ranges"),
        description=_(u"Contains the listed value ranges"),
        value_type=zope.schema.Tuple(
            title=u"Range",
            min_length=2,
            max_length=2,
            value_type=zope.schema.Float(title=_(u"Value")),
            ),
        required=False,
        )
