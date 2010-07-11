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

_ = MessageFactory(__name__)

# -----------------------------------------------------------------------------
# BASE INTERFACES
# -----------------------------------------------------------------------------

class IBase(Interface):
    """
    Base interface class for all interfaces under this add-on module.
    
    TODO Rename to something more meaningful.
    """

# -----------------------------------------------------------------------------
# API INTERFACES
# -----------------------------------------------------------------------------

class IDataSource(IBase):
    """
    """
    
    fia = schema.TextLine(
        title=_(u"The DSN for the FIA database.")
        )

    pii = schema.TextLine(
        title=_(u"The DSN for the PII database.")
        )    

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
        title=_(u"State")
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


    