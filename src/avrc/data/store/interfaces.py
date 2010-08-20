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
#
# -----------------------------------------------------------------------------

class Versionable(Interface):
    """
    """

    __version__ = Attribute(_(u"This will be used to keep track of the "
                              u"data store schema as they evolve"))

class Formable(Interface):
    """
    Represents a schema that contains detailed information for display in a
    form.
    """

    __title__ = Attribute(_(u"A way to represent the name of in the form"))

    __description__ = Attribute(_(u"A way to represent the description."))

    __dependents__ = Attribute(_(u"Dependent schemata"))

class Schema(Versionable, Formable):
    """
    Marker interface for a schema maintained by the data store.
    """

# -----------------------------------------------------------------------------
# API CONTRACTS
# -----------------------------------------------------------------------------

class IComponent(Interface):
    """
    Base interface for the components of this package.
    """

class IRange(IComponent, zope.schema.interfaces.ITuple):
    """
    A custom schema type in order to support built-in range values.
    """

    low = zope.schema.Int(
        title=_(u"Low Value"),
        required=True
        )

    high = zope.schema.Int(
        title=_(u"High Value"),
        required=True
        )

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
            The purged object, None otherwise (nothing to purge)
        """

    def retire(key):
        """
        Retires the contained target. This means that it's information remains,
        only it's not visible anymore. The reason this functionality is useful
        is so that data can be 'brought back' if expiring caused undesired
        side-effects.

        Arguments:
            key: an item that can be used to find the component in the manager.
        Returns:
            The retired object, None otherwise (nothing to retired)
        """

    def restore(key):
        """
        Attempts to restore a previously retired object via its key handle.

        Arguments:
            key: an item that can be used to find the component in the manager.
        Returns:
            The restored object, None otherwise (nothing to restore)
        """

    def put(target):
        """
        Adds or modifies the target into the manager

        Arguments:
            target: an object that will be added to this component's manager.
        Returns:
            A key to the newly stored target
        Raises:
            TODO: needs to raise something if put fails.
        """

class ISchemaManager(IManager):
    """
    Marker interface for managing schemata.
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
        required=True
        )

    dsn = zope.schema.TextLine(
        title=_(u"Data Source Name"),
        description=_(u"URL of the database to use for physical storage."),
        required=True
        )

class ISessionFactory(IComponent, IContained):
    """
    Used for implementing our own SQLAlchemy session. The reason for using our
    own Interface instead of a third party's such as z3c.saconfig is because
    we need more control over our session (e.g. need multiple engines
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

    value = Attribute(_(u"A way to distinguish this item in the data store"))

class IDomain(IComponent):
    """
    """
    zid = zope.schema.Int(title=_(u"Domain Zope IntId"))

    code = zope.schema.TextLine(title=_(u"Code"))

    title = zope.schema.TextLine(title=_(u"Title"))

    consent_date = zope.schema.Date(title=_(u"Date of consent"))


class IProtocol(IComponent):
    """
    """
    zid = zope.schema.Int(title=_(u"Protocol Zope IntId"))

    cycle = zope.schema.Int(title=_(u"Protocol Cycle"))

    domain_zid = zope.schema.Int(title=_(u"Domain Zope IntId"))

    threshold = zope.schema.Int(title=_(u"Cycle Threshold"))

    is_active = zope.schema.Bool(title=_(u"Active?"))


class IVisit(IComponent):
    """
    """
    zid = zope.schema.Int(title=_(u"Visit Zope IntId"))

    visit_date = zope.schema.Date(title=_(u"Visit Date"))

    enrollment_zids = zope.schema.List(title=_(u"Enrollment Zope IntIds"),
                                       value_type=zope.schema.Int(title=_(u"Zope Id"))
                                       )
    protocol_zids = zope.schema.List(title=_(u"Protocol Zope IntIds"),
                                       value_type=zope.schema.Int(title=_(u"Zope Id"))
                                       )

class IEnrollment(IComponent):
    """
    """
    zid = zope.schema.Int(title=_(u"Enrollment Zope IntId"))

    subject_zid = zope.schema.Int(title=_(u"Enrolled Subject Zope IntId"))

    domain_zid = zope.schema.Int(title=_(u"Enrolled Domain Zope IntId"))

    start_date = zope.schema.Date(title=_(u"Initial Date of Consent"))

    consent_date = zope.schema.Date(title=_(u"Latest Date of Consent"))

    stop_date = zope.schema.Date(title=_(u"End Date"))

class ISubject(IComponent):
    """
    """
    uid = zope.schema.Int(title=_("OUR Number"))
    
    zid = zope.schema.Int(title=_("Subject Zope IntId"))

    nurse_email = zope.schema.TextLine(title=_("Subject's Primary Nurse"))


class IReportable(IComponent):
    """
    Promises to do some form of reporting.
    """

    def report():
        """
        """

class IQueryLine(IComponent):
    """
    A simple query to the data store.
    """
    value = zope.schema.TextLine(
        title=_(u"Search"),
        required=True
        )

class IQuery(IComponent):
    """
    Querying contract.
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

class IConventionalManager(IManager):
    """
    Marker interface for managing domains
    """
#    datastore = zope.schema.Object(title=u"Datastore",
#                                   schema=IDatastore)
#    _type = zope.schema.Object(title=u"Type",
#                               value_type=IManager)

class IDomainManager(IManager):
    """
    Marker interface for managing domains
    """

class ISubjectManager(IManager):
    """
    Marker interface for managing subjects
    """

class IProtocolManager(IManager):
    """
    Marker interface for managing protocols
    """

class IEnrollmentManager(IManager):
    """
    Marker interface for managing enrollments
    """

class IVisitManager(IManager):
    """
    Marker interface for managing protocols
    """
