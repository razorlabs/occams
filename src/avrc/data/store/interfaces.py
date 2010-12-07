""" Exposes specification for the components that will make up the data store
    package.

    Note that not all of the functionality will currently be in place, but this
    is a good area to specify all the components that would be nice to have in
    the long term.
"""

import zope.interface
import zope.schema
from zope.location.interfaces import IContained

from plone.directives import form

from avrc.data.store import MessageFactory as _

# -----------------------------------------------------------------------------
# ERRORS
# -----------------------------------------------------------------------------

class Error(Exception):
    """Base class for all errors in this package """

class DatatoreError(Error):
    """Base class for data store-related errors """

class SchemaError(Error):
    """Base class for schema-related errors """

class UndefinedSchemaError(Error):
    """Raised when trying to access a schema that is not in the data store """

# -----------------------------------------------------------------------------
# API
# -----------------------------------------------------------------------------

class IComponent(zope.interface.Interface):
    """ Base interface for the components of this package. """

class Versionable(IComponent):
    """ TODO/NOTE: We should just implement these as class directives in order
                   prevent interface property pollution.
    """

    __version__ = zope.interface.Attribute(
        _(u"This will be used to keep track of the "
          u"data store schema as they evolve"))

class Formable(IComponent, form.Schema ):
    """ Represents a schema that contains detailed information for display in a
        form.

        TODO/NOTE: We should just implement these as class directives in order
            prevent interface property pollution.
    """

    __title__ = zope.interface.Attribute(
        _(u"A way to represent the name of in the form"))

    __description__ = zope.interface.Attribute(
        _(u"A way to represent the description."))

    __dependents__ = zope.interface.Attribute(
        _(u"Dependent schemata"))

class Schema(Versionable, Formable):
    """ Marker interface for a schema maintained by the data store. """

class IRange(IComponent, zope.schema.interfaces.ITuple):
    """ A custom schema type in order to support built-in range values. """

    low = zope.schema.Int(
        title=_(u"Low Value"),
        required=True
        )

    high = zope.schema.Int(
        title=_(u"High Value"),
        required=True
        )

class IManager(IComponent):
    """ Specification for management components, that is, components that are in
        charge of a particular class of data. Note that a manager is simply a
        utility into to the data store, therefore creating multiple instances
        of a manager should have no effect on the objects being managed as they
        are still being pulled from the same source.
    """

    def keys():
        """ Generates a collection of the keys for the objects the component is
            managing.

            Returns:
                A listing of the object keys being managed by this manager.
        """

    def has(key):
        """ Checks if the component is managing the item.

            Arguments:
                key: an item that can be used to find the component in
                    the manager.

            Returns:
                True if the manager is in control of the item.
        """

    def get(key):
        """ Arguments:
                key: an item that can be used to find the component in
                    the manager.
            Returns:
                An object maintained by the manger. None if not found.
        """

    def purge(key):
        """ Completely removes the target and all data associated with it
            from the data store.

            Arguments:
                key: an item that can be used to find the component in
                    the manager.
            Returns:
                The purged object, None otherwise (nothing to purge)
        """

    def retire(key):
        """ Retires the contained target. This means that it's information
            remains, only it's not visible anymore. The reason this
            functionality is useful is so that data can be 'brought back'
            if expiring caused undesired side-effects.

            Arguments:
                key: an item that can be used to find the component in
                    the manager.
            Returns:
                The retired object, None otherwise (nothing to retired)
        """

    def restore(key):
        """ Attempts to restore a previously retired object via its key handle.

            Arguments:
                key: an item that can be used to find the component in
                    the manager.
            Returns:
                The restored object, None otherwise (nothing to restore)
        """

    def put(target):
        """ Adds or modifies the target into the manager

            Arguments:
                target: an object that will be added to this component's manager.
            Returns:
                A key to the newly stored target
            Raises:
                TODO: needs to raise something if put fails.
        """

class ISchemaManager(IManager):
    """ Marker interface for managing schemata. """

    def get_descendants(iface):
        """ Retrieves the classes that inherit from the specified base.

            Arguments:
                iface: (object) base interface to find all the descendants for
            Returns:
                list of interfaces that extend the specified base
        """

    def get_children(iface):
        """ Retrieves all the children of the base class. Note this does
            not include all the intermediate bases (i.e. it just returns the
            leaf nodes)

            Arguments:
                iface: (object) base interface to find all the children for
            Returns:
                list of interfaces that extend the specified base
        """

class IDatastore(IManager):
    """ Represents a data store utility that can be added to a site. It is in
        charge of managing the entire network of data that will be created from
        schemata, etc. It achieves this by using registered helper utilities
        that it adapts into called "managers".
    """

    session = zope.schema.TextLine(
        title=_(u"Session Utility Name"),
        description=_(u"The name of the z3c.saconfig session to use."),
        required=True
        )

    def spawn(iface, **kw):
        """ Generates an object that implements the specified schema
        """

    def getManager(imanager):
        """ Get the specified management utility assigned to this datastore.

            Arguments:
                imanager: (object) zope interface specification of the utility
                    to retrieve
            Returns:
                A management utility that implements the request specification
        """

    def getAliquotManager():
        """
        """

    def getSpecimenManager():
        """
        """

    def getDomainManager():
        """
        """

    def getEnrollmentManager():
        """
        """

    def getProtocolManager():
        """
        """

    def getSchemaManager():
        """
        """

    def getSubjectManager():
        """
        """

    def getVisitManager():
        """
        """

    def getDrugManager():
        """
        """

    def getMedicationManager():
        """
        """

    def getPartnerManager():
        """
        """

class IInstance(IComponent):
    """ Empty object that will be used as the instance of a virtual schema. """

    __id__ = zope.interface.Attribute(
        _(u"The INTERNAL id of the instance. Tampering or "
          u"accessing this id outside of this package is "
          u"highly not recommended"))

    title = zope.interface.Attribute(_(u"The instance's database-unique name"))

    description = zope.interface.Attribute(_("A description for the object"))

class IKey(IComponent):
    """ Ideally, this interface should be used to somehow manage identifiers for
        the managers. But, in it's current state this interface is unused...
    """

    value = zope.interface.Attribute(
        _(u"A way to distinguish this item in the data store"))

class IDomain(IComponent):
    """ """
    zid = zope.schema.Int(title=_(u"Domain Zope IntId"))

    code = zope.schema.TextLine(title=_(u"Code"))

    title = zope.schema.TextLine(title=_(u"Title"))

    consent_date = zope.schema.Date(title=_(u"Date of consent"))


class IProtocol(IComponent):
    """ """
    zid = zope.schema.Int(title=_(u"Protocol Zope IntId"))

    cycle = zope.schema.Int(title=_(u"Protocol Cycle"))

    domain_zid = zope.schema.Int(title=_(u"Domain Zope IntId"))

    threshold = zope.schema.Int(title=_(u"Cycle Threshold"), required=False)

    is_active = zope.schema.Bool(title=_(u"Active?"), required=False)


class IVisit(IComponent):
    """ """
    zid = zope.schema.Int(title=_(u"Visit Zope IntId"))

    enrollment_zids = zope.schema.List(
       title=_(u"???"),
       value_type=zope.schema.Int(title=_(u"???"))
       )

    protocol_zids = zope.schema.List(
       title=_(u"???"),
       value_type=zope.schema.Int(title=_(u"???"))
       )

    visit_date = zope.schema.Date(title=_(u"Visit Date"))

class IEnrollment(IComponent):
    """ """
    zid = zope.schema.Int(title=_(u"Enrollment Zope IntId"))

    subject_zid = zope.schema.Int(title=_(u"Enrolled Subject Zope IntId"))

    domain_zid = zope.schema.Int(title=_(u"Enrolled Domain Zope IntId"))

    start_date = zope.schema.Date(title=_(u"Initial Date of Consent"))

    consent_date = zope.schema.Date(title=_(u"Latest Date of Consent"))

    stop_date = zope.schema.Date(title=_(u"End Date"))

    eid = zope.schema.TextLine(title=_(u"Enrollment Identifier"), required=False)

class ISubject(IComponent):
    """ """
    zid = zope.schema.Int(title=_("Zope's ID"))

    nurse_email = zope.schema.TextLine(title=_(u"Nurse's email"))

    uid = zope.schema.Int(title=_("OUR Number"))

    aeh = zope.schema.TextLine(title=_("Legacy AEH number"), required=False)

class IReportable(IComponent):
    """ Promises to do some form of reporting. """

    def report():
        """ """

class IQueryLine(IComponent):
    """ A simple query to the data store. """

    value = zope.schema.TextLine(
        title=_(u"Search"),
        required=True
        )

class IQuery(IComponent):
    """ Querying contract. """

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
    """ Marker interface for managing domains """

#    datastore = zope.schema.Object(title=u"Datastore",
#                                   schema=IDatastore)
#    _type = zope.schema.Object(title=u"Type",
#                               value_type=IManager)

class IDomainManager(IManager):
    """ Marker interface for managing domains """

class ISubjectManager(IManager):
    """ Marker interface for managing subjects """

class IProtocolManager(IManager):
    """ Marker interface for managing protocols """

class IEnrollmentManager(IManager):
    """ Marker interface for managing enrollments """

class IVisitManager(IManager):
    """ Marker interface for managing protocols """

class ISpecimenManager(IManager):
    """ Marker interface for managing specimen """

    def list(start=None, num=None):
        """ """

class IAliquotManager(IManager):
    """ Marker interface for managing specimen """

    def list(start=None, num=None):
        """ """

class ISpecimen(IComponent):
    """ Mostly copied from aeh forms. Tons of work to do still. """

    dsid = zope.schema.Int(
        title=_(u"Data Store Id"),
        required=False,
        readonly=True
        )

    subject_zid = zope.schema.Int(title=_(u"Enrolled Subject Zope IntId"))

    protocol_zid = zope.schema.Int(title=_(u"Protocol's Zope IntId"))

    state = zope.schema.TextLine(
        title=_(u"State"),
        )

    date_collected = zope.schema.Date(
        title=_(u"Date & Time Collected"),
        required=False,
        )

    time_collected = zope.schema.Time(
        title=_(u"Date & Time Collected"),
        required=False,
        )

    specimen_type = zope.schema.TextLine(
        title=_(u"Specimen Type"),
        )

    destination = zope.schema.TextLine(
        title=_(u"Destination"),
        )

    tubes = zope.schema.Int(
        title=_(u"How many tubes?"),
        required=False,
        )

    tube_type = zope.schema.TextLine(
        title=_(u"Tube Type"),
        )

    notes = zope.schema.Text(
        title=_(u"Notes"),
        required=False,
        )

class IAliquot(IComponent):
    """ Mostly copied from aeh forms. Tons of work to do still. """

    dsid = zope.schema.Int(
        title=_(u"Data Store Id"),
        required=False,
        )

    specimen_dsid = zope.schema.Int(
        title=_(u"Data Store Specimen Id"),
        required=False,
        )
    type = zope.schema.TextLine(
        title=_(u"Type"),
        )

    state = zope.schema.TextLine(
        title=_(u"State"),
        required=False
        )

    volume = zope.schema.Float(
        title=u"Volume (in ml.)",
        required=False,
        )

    cell_amount = zope.schema.Float(
        title=_(u"Number of cells"),
        description=_(u"measured in 10,000 increments"),
        required=False,
        )

    store_date = zope.schema.Date(
        title=_(u"Store Date"),
        required=False
        )

    freezer = zope.schema.TextLine(
        title=_(u"Freezer"),
        required=False,
        )

    rack = zope.schema.TextLine(
        title=_(u"Rack"),
        required=False,
        )

    box = zope.schema.TextLine(
        title=_(u"Box"),
        required=False,
        )

    thawed_num = zope.schema.Int(
        title=_(u"Number of times thawed."),
        required=False,
        )

    analysis_status = zope.schema.TextLine(
        title=_(u"Sent for analysis?"),
        required=False
        )

    sent_date = zope.schema.Date(
        title=_(u"Date sent"),
        required=False
        )

    storage_site = zope.schema.TextLine(
        title=_(u"Enter the site where aliquot was sent"),
        required=False
        )

    sent_name = zope.schema.TextLine(
        title=_(u"Please enter the name of the person the aliquot was sent to "
                u"OR the name of the person who placed the sample "
                u"on hold:"),
        required=False,
        )

    notes = zope.schema.Text(
        title=_(u"Notes on this aliquot (if any):"),
        required=False
        )

    special_instruction = zope.schema.TextLine(
        title=_(u"Special"),
        description=u"",
        required=False,
        )


class IMedication(IComponent):
    """ Content-type for adding current medications to a patient.
    """

    dsid = zope.schema.Int(title=_(u'Datastore ID'), required=False)

    subject_zid = zope.schema.Int(title=_(u'Zope Subject Object ID'))

    drug_code = zope.schema.TextLine(
        title=_(u'Drug Code'),
        required=True
        )

    start_date = zope.schema.Date(
        title=_(u'Date Started'),
        description=_(u'Date the patient started taking the drug.'),
        required=True
        )

    stop_date = zope.schema.Date(
        title=_(u'Date Stopped'),
        description=_(u'Date the patient stopped taking the drug.'),
        required=False
        )
    notes = zope.schema.Text(
        title=_(u"Notes (if any):"),
        required=False
        )


class IDrugManager(IManager):
    """
    """

    def import_(drug_list):
        """
        """


    def getCodesVocabulary():
        """
        """


class IMedicationManager(IManager):
    """
    """

    def listByVisit(visit, subject):
        """
        """


    def listBySubject(subject):
        """
        """


class IPartnerManager(IManager):
    """
    """


class IPartner(IComponent):
    """
    """

    zid = zope.schema.Int(title=_(u'Zope Object ID'))

    subject_zid = zope.schema.Int(title=_(u'Subject Object ID'))

    enrolled_subject_zid = zope.schema.Int(title=_(u'Enrolled Subject Object ID'))

    visit_date = zope.schema.Date(title=_(u'Recorded Visit Date'))


class ISymptom(IComponent):
    """ Content-type for adding current medications to a patient.
    """

    dsid = zope.schema.Int(title=_(u'Datastore ID'), required=False)

    subject_zid = zope.schema.Int(title=_(u'Zope Subject Object ID'))

    type = zope.schema.TextLine(
        title=_(u'Type'),
        required=True
        )

    is_present = zope.schema.Bool(
        title=_(u'Present?'),
        required=True,
        )

    status = zope.schema.TextLine(
        title=_(u'Status'),
        required=True
        )

    start_date = zope.schema.Date(
        title=_(u'Date Started'),
        description=_(u'Date the patient started taking the drug.'),
        required=True
        )

    stop_date = zope.schema.Date(
        title=_(u'Date Stopped'),
        description=_(u'Date the patient stopped taking the drug.'),
        required=False
        )
    notes = zope.schema.Text(
        title=_(u"Notes (if any):"),
        required=False
        )


class ISymptomManager(IManager):
    """
    """

    def importTypes(symptom_types):
        """ The symptom types aren't a a type yet (unlike, say `Drug`), so
            they don't need their own manager.
        """

    def importStatuses(symptom_statuses):
        """ The symptom types aren't a a type yet (unlike, say `Drug`), so
            they don't need their own manager.
        """


    def getTypesVocabulary():
        """
        """

    def getStatusVocabulary():
        """
        """


    def listByVisit(visit, subject):
        """
        """


    def listBySubject(subject):
        """
        """

