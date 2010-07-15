"""
Defines the interfaces for the objects that will be regarded as Personnally
Identifiable Information. Ideally, this information should not be stored
alongside all gathered data in a protocol, as this would violate privacy
policies. Instead, implementations should use a reference number to
communicate between data objects and privacy objects.
"""

from zope.interface import Interface
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
# API CONTRACT INTERFACES
# -----------------------------------------------------------------------------
    
class IDataStore(IBase, IContained):
    """
    Represents a Data Store instance that can be added to a site. Currently
    only one Data Store per site is supported.
    
    Zope Products that wish to use this library should implement this
    interface.
    """

    pii = schema.TextLine(
        title=_(u"The DSN for the PII database. Note that if none is "
                u"specified, the FIA connection string will be used."),
        required=False
        )
    
    fia = schema.TextLine(
        title=_(u"The DSN for the FIA database.")
        )


# -----------------------------------------------------------------------------
# LIBRARY INTERFACES
# -----------------------------------------------------------------------------


class ISessionFactory(IBase):
    """
    Used for implementing our own SQLAlchemy session. The reason for using our
    own Interface instead of a third party's such as z3c.saconfig is because
    we need more control over our sesession (e.g. need multiple engines
    per Session as opposed to the single engine allowed by z3c.saconfig"
    """
    
    autocommit = schema.Bool(
        title=_(u"Auto Commit Enabled"),
        description=_(u"If set, new objects that are added to the session "
                      u"will be automatically persisted in the underlying "
                      u"database."),
        default=False
        )
    
    autoflush = schema.Bool(
        title=_(u"Auto Flush Enabled"),
        description=_(u"If set, objects will automatically be retrieved from "
                      u"the database in order to synchronize themselves."),
        default=True,
        )
    
    two_phase = schema.Bool(
        title=_(u"Two Phase Enabled"),
        description=_(u"See SQLAlchemy documentation...")
        )

    def __call__(self):
        """
        Returns the generated SQLAlchemy Session
        """
    

# -----------------------------------------------------------------------------
# MARKER INTERFACES
# -----------------------------------------------------------------------------

class IInternal(IBase):
    """
    Marker interface for information that will be regarded as Personally
    Identifiable Information for objects that are stored. This information
    should be kept "Internal" to the client product in order to protect the
    privacy of it's subjects.
    """
    
    
class IAccessible(IBase):
    """
    Marker interface for information that can be publicly accessible to parties
    that give permissions to. This information should be completely devoid of
    personally identifiable information, such information should be kept 
    internal using a separate module implementing the IInternal interface.
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
    
    number = schema.Int(
        title=_(u"")
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
# PERSONAL INFORMATION INTERFACES
# -----------------------------------------------------------------------------

class IContact(IInternal):
    """
    Represents conntact information that can apply to a reference.
    """
    
    phone = schema.TextLine(
        title=_(u"Phone Number")
        )
    
    address1 = schema.TextLine(
        title=_(u"Line 1")
        )

    address2 = schema.TextLine(
        title=_(u"Line 2")
        )

    city = schema.TextLine(
        title=_(u"City")
        )
    
    state = schema.Choice(
        title=_(u"State"),
        vocabulary="states"
        )
    
    zip = schema.Int(
        title=_(u"ZIP Code")
        )


class IName(IInternal):
    """
    Represents a name than can apply to a reference.
    """
    
    first = schema.TextLine(
        title=_(u"First Name")
        )
    
    middle = schema.TextLine(
        title=_(u"Middle Name"),
        )
    
    last = schema.TextLine(
        title=_(u"Last Name")
        )
    
    sur = schema.TextLine(
        title=_(u"Surname")
        )


class IDemographic(IInternal):
    """
    Represents demographic information about a reference
    """
    
    birthdate = schema.Date(
        title=_(u"Birth Date")
        )
    
# -----------------------------------------------------------------------------
# PUBLICLY ACCESSIBLE INTERFACES
# -----------------------------------------------------------------------------


    