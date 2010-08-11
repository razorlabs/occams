"""
Contains specification as to how data will be stored and managed.
"""

from zope.interface import Interface, Attribute

from zope import schema
from zope.i18nmessageid import MessageFactory

from zope.app.container.interfaces import IContained

_ = MessageFactory(__name__)

# -----------------------------------------------------------------------------
# BASE INTERFACES
# -----------------------------------------------------------------------------

class IBase(Interface):
    """
    Convenience marker interface to serve as a base class for all interfaces
    of this package.
    """

# -----------------------------------------------------------------------------
# ERRORS
# -----------------------------------------------------------------------------

class Error(Exception):
    """Base class for all errors in this package"""

class DatatoreError(Error):
    """Base class for datastore-related errors"""

class SchemaError(Error):
    """Base class for schama-related errors"""

class UndefinedSchemaError(Error):
    """Raised when trying to access a schema that is not in the datastore"""

# -----------------------------------------------------------------------------
# API CONTRACT INTERFACES
# -----------------------------------------------------------------------------

class IManager(IBase):
    """
    Base class for all managers
    """

    def keys():
        """
        Returns a listing of the object keys being managed by this manager.
        """

    def has(key):
        """
        """

    def get(key):
        """
        Return an object contained by the manager based on it's identification
        value.
        """

    def purge(key):
        """
        Completely removes the target and all data associated with it from the
        data store.
        """

    def retire(key):
        """
        Expire's the contained target. This means that it's information remains,
        only it's not visible anymore. The reason this functionality is useful
        is so that data can be 'brought back' if expiring caused undesired
        side-effects.
        """

    def put(target):
        """
        Adds or modifies the target into the manager
        """

class IStorageManager(IManager):
    """
    Marker interface for managing data objects.
    """

class IEnrollmentManager(IManager):
    """
    Marker interface for managing enrollments
    """

class ISchemaManager(IManager):
    """
    Marker interface for managing schemas
    """

class IKeywordManager(IManager):
    """
    Marker interface for managing keyword associations with objects
    """

class IAttributeManager(IManager):
    """
    Marker interface for managing attributes
    """

class IVocabularyManager(IManager):
    """
    Marker interface for managing vocabularies
    """

class IDomainManager(IManager):
    """
    Marker interface for managing domains
    """

class IMutableSchema(IBase):
    """
    This is used when the schemata are going to be modified.
    """

class IDatastore(IManager, IContained):
    """
    Represents a datastore instance that can be added to a site.
    """

    title = schema.TextLine(
        title=_(u"The name of the data store"),
        description=_(u""),
        )

    dsn = schema.TextLine(
        title=_(u"Something cool about dsns"),
        description=_("Something descripting about dsns")
        )

class ISessionFactory(IBase):
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

class IInstance(IBase):
    """
    """

    __schema__ = Attribute(_(u"The specific schema this is an instance of "
                             u"including the medata/version/etc"
                             ))

class IKey(IBase):
    """
    """

    __key__ = Attribute(_(u"A way to distinguish this item in the data store"))

class IVersionable(IBase):
    """
    """

    __version__ = Attribute(_(u"This will be used to keep track of the "
                              u"data store schema as they evolve"))

class IFormable(IBase):
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

# -----------------------------------------------------------------------------
# REFERENCES
# -----------------------------------------------------------------------------

class ISubject(IBase):
    """
    A subject that that will be associated with attributes. This will also
    serve as a way for both Internal and Accessible data to communicate
    about a subject.
    """

    id = schema.Int(
        title=_(u"Identification Number"),
        description=_(u"")
        )

class IReference(IBase):
    """
    An reference identifier for a subject. This object is intended for legacy
    identifiers from previous systems.
    """

    name = schema.TextLine(
        title=_(u"Name"),
        description=_(u"The name of the reference.")
        )

    number = schema.TextLine(
        title=_(u"Number"),
        description=_("The number given to the subject under the reference.")
        )

# -----------------------------------------------------------------------------
# LIBRARY INTERFACES
# -----------------------------------------------------------------------------

class IDomain(IBase):
    """
    TESTING: supposed to offer the domain functionality
    """

    title = schema.TextLine(
        title=_(u"Title")
        )

class IReportable(IBase):
    """
    Interface for generatged schema Promises to do some form of reporting
    """

    def report():
        """
        """

class IField(IBase):

    min = schema.Int(title=u"Minimum Value")

    max = schema.Int(title=u"Maximum Value")

# -----------------------------------------------------------------------------
# QUERYING
# -----------------------------------------------------------------------------

class IQueryLine(IBase):
    """
    """
    value = schema.TextLine(
        title=_(u"Search"),
        )

class IQuery(IBase):
    """
    Querying contract.
    STILL IN PLANNING STAGES
    """

    contains = schema.List(
        title=_(u"Phrases"),
        description=_(u"Contains any of the listed terms."),
        value_type=schema.TextLine(title=_(u"Phrase")),
        required=False,
        )

    some = schema.List(
        title=_(u"Some Phrases"),
        description=_("Contains one or more of the listed terms."),
        min_length=1,
        max_length=3,
        value_type=schema.TextLine(title=_(u"Phrase")),
        required=False,
        )

    ignore = schema.List(
        title=_(u"Do not include"),
        description=_(u"Do not include the listed terms."),
        value_type=schema.TextLine(title=_(u"Phrase")),
        required=False,
        )

    domain = schema.List(
        title=_(u"Domain search"),
        description=_(u"Search within a domain only."),
        value_type=schema.TextLine(title=_(u"Phrase")),
        required=False,
        )

    date = schema.Choice(
        title=_(u"Date"),
        description=_(u"How recent is the entry?"),
        values=(_(u"anytime"),
                _(u"past 24 hours"),
                _(u"past week"),
                _(u"past month"),
                _(u"past year")),
        required=False
        )

    range = schema.List(
        title=_(u"Numeric ranges"),
        description=_(u"Contains the listed value ranges"),
        value_type=schema.Tuple(
            title=u"Range",
            min_length=2,
            max_length=2,
            value_type=schema.Float(title=_(u"Value")),
            ),
        required=False,
        )
