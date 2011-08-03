
import zope.interface
import zope.schema

from avrc.data.store.interfaces import IManager
from avrc.data.store import MessageFactory as _


class IClinicalMarker(zope.interface.Interface):
    """
    """


class IDomain(IClinicalMarker):
    """ """
    zid = zope.schema.Int(title=_(u'Domain Zope IntId'))

    code = zope.schema.TextLine(title=_(u'Code'))

    title = zope.schema.TextLine(title=_(u'Title'))

    consent_date = zope.schema.Date(title=_(u'Date of consent'))


class IProtocol(IClinicalMarker):
    """ """
    zid = zope.schema.Int(title=_(u'Protocol Zope IntId'))

    cycle = zope.schema.Int(title=_(u'Protocol Cycle'), required=False)

    domain_zid = zope.schema.Int(title=_(u'Domain Zope IntId'))

    threshold = zope.schema.Int(title=_(u'Cycle Threshold'), required=False)

    is_active = zope.schema.Bool(title=_(u'Active?'), required=False, default=True)


class IVisit(IClinicalMarker):
    """ """
    zid = zope.schema.Int(title=_(u'Visit Zope IntId'))

    subject_zid = zope.schema.Int(title=_(u'Enrolled Subject Zope IntId'))

    protocol_zids = zope.schema.List(
       title=_(u'???'),
       value_type=zope.schema.Int(title=_(u'???'))
       )

    visit_date = zope.schema.Date(title=_(u'Visit Date'))


class IEnrollment(IClinicalMarker):
    """ """
    zid = zope.schema.Int(title=_(u'Enrollment Zope IntId'))

    subject_zid = zope.schema.Int(title=_(u'Enrolled Subject Zope IntId'))

    domain_zid = zope.schema.Int(title=_(u'Enrolled Domain Zope IntId'))

    start_date = zope.schema.Date(title=_(u'Initial Date of Consent'))

    consent_date = zope.schema.Date(title=_(u'Latest Date of Consent'))

    stop_date = zope.schema.Date(title=_(u'End Date'))

    eid = zope.schema.TextLine(title=_(u'Enrollment Identifier'), required=False)


class ISubject(IClinicalMarker):
    """ """
    zid = zope.schema.Int(title=_('Zope\'s ID'))

    nurse_email = zope.schema.TextLine(title=_(u'Nurse\'s email'))

    uid = zope.schema.Int(title=_('Encoded OUR Number (deprecated)'))

    our = zope.schema.TextLine(title=_('OUR Number'))

    aeh = zope.schema.TextLine(title=_('Legacy AEH number'), required=False)


class IPartner(IClinicalMarker):
    """
    """

    zid = zope.schema.Int(title=_(u'Zope Object ID'))

    subject_zid = zope.schema.Int(title=_(u'Subject Object ID'))

    enrolled_subject_zid = zope.schema.Int(title=_(u'Enrolled Subject Object ID'))

    visit_date = zope.schema.Date(title=_(u'Recorded Visit Date'))


class IDomainManager(IManager):
    """ Marker interface for managing domains """


class ISubjectManager(IManager):
    """ Marker interface for managing subjects 
    """


class IProtocolManager(IManager):
    """ Marker interface for managing protocols 
    """


class IEnrollmentManager(IManager):
    """ Marker interface for managing enrollments 
    """


class IVisitManager(IManager):
    """ Marker interface for managing protocols 
    """


class IPartnerManager(IManager):
    """ Marker interface for managing subject partners.
    """
