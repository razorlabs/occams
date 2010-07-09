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

class IPII(Interface):
    """
    Marker interface for information that will be regarded as Personally
    Identifiable Information for objects that are stored.
    """
    

class IReference(IPII):
    """
    The number that is used to keep track of the 
    """
    
    number = schema.Int(
        title=_(u"")
        )


class IExternal(IPII):
    """
    An external resource identifier. This object is intended for legacy
    identifiers from previous systems.
    """
    
    name = schema.TextLine(
        title=_(u"Name"),
        description=_(u"The name of the external source.")
        )
    
    number = schema.TextLine(
        title=_(u"Number"),
        description=_("The reference number of the external source.")
        )


class IContact(IPII):
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


class IName(IPII):
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


class IDemographic(IPII):
    """
    Represents demographic information about a reference
    """
    
    birthdate = schema.Date(
        title=_(u"Birth Date")
        )
    