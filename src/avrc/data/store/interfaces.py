"""
Contains specification as to how data will be stored and managed.
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
    
class IManager(IBase):
    """
    Base class for all managers
    """
    
    def add(target):
        """
        Adds the target to the manager
        """
        
    def get(id):
        """
        Return an object contained by the manager based on it's identification
        value. 
        """
        
    def modify(target):
        """
        Updates the original object the the target's properties
        """
        
    def expire(target):
        """
        Expire's the contained target. This means that it's information remains,
        only it's not visible anymore. The reason this functionality is useful
        is so that data can be 'brought back' if expiring caused undesired
        side-effects.
        """
        
    def remove(target):
        """
        Completely removes the target and all data associated with it from the
        data store.
        """
        
    def list():
        """
        Returns a listing of the objects being managed by this manager.
        """
    
class IEngine(IBase, IContained):
    """
    Represents a Data Store instance that can be added to a site. 
    """

    pii_dsn = schema.TextLine(
        title=_(u"Personally Identifiable Information Data Source Name"),
        description=_(u"The Data Source Name (DSN) for database that will "
                      u"contain information regarded as Personally " 
                      u"Identifiable Information (PII). "
                      u"This is a feature that is required for clinical "
                      u"studies. If none is specified, the FIA DSN will be "
                      u"used. Note that it is up to the vendor using this "
                      u"library to take proper measures in making sure that "
                      u"the data source is secure. "
                      u"If unspecified, the FIA DSB will be used."),
        required=False
        )
    
    fia_dsn = schema.TextLine(
        title=_(u"Freedom of Information Act Data Source Name"),
        description=_(u"The Data Source Name (DSN) for the database that will "
                      u"contain information that can be disclosed to trusted "
                      u"parties.")
        )
    
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
    
class ISchema(IBase): 
    """
    """

    namespace = schema.DottedName(
        title=_(u"Namespace"),
        description=_(u"The fully qualified name of the package")
        )
    
    def set_parent():
        """
        """
    
    def set_attribute(attribute):
        """
        """
        
class IVesion(IBase):
    """
    """
    
    # TODO: check base interface to see if this is already provided
    __version__ = schema.TextLine(
        title=_(u""),
        description=_(u"")
        )
        
class IAttribute(IBase):
    """
    """

class IInstance(IBase):
    """
    """

# -----------------------------------------------------------------------------
# MARKER INTERFACES
# -----------------------------------------------------------------------------

class IPII(IBase):
    """
    Marker interface for information that will be regarded as Personally
    Identifiable Information for objects that are stored. This information
    should be kept "Internal" to the client product in order to protect the
    privacy of it's subjects.
    """
    
class IFIA(IBase):
    """
    Marker interface for information that can be publicly accessible to parties
    that give permissions to. This information should be completely devoid of
    personally identifiable information, such information should be kept 
    internal using a separate module implementing the IPII interface.
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
    TESTING: supposed to offert the domain functionality
    """

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

# -----------------------------------------------------------------------------
# PERSONAL INFORMATION INTERFACES
# -----------------------------------------------------------------------------

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
        title=_(u"State"),
        vocabulary="states"
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
    