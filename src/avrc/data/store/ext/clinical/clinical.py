""" Clinical object and utilities.
"""

from zope.component import adapts
from zope.schema.fieldproperty import FieldProperty
from zope.interface import implements
from zope.interface import classProvides

import sqlalchemy as sa
from sqlalchemy import orm

from avrc.data.store.directives import Schema
from avrc.data.store.storage import Item
from avrc.data.store.ext.clinical.manager import ConventionalManager
from avrc.data.store.ext.clinical.manager import EAVContainerManager
from avrc.data.store.interfaces import IDataStore


from avrc.data.store.interfaces import IDataStoreExtension
from avrc.data.store.ext.clinical.interfaces import ISubject
from avrc.data.store.ext.clinical.interfaces import IPartner
from avrc.data.store.ext.clinical.interfaces import IEnrollment
from avrc.data.store.ext.clinical.interfaces import IVisit
from avrc.data.store.ext.clinical.interfaces import IPartnerManager
from avrc.data.store.ext.clinical.interfaces import ISubjectManager
from avrc.data.store.ext.clinical.interfaces import IEnrollmentManager
from avrc.data.store.ext.clinical.interfaces import IVisitManager
from avrc.data.store.ext.clinical.interfaces import IDomain
from avrc.data.store.ext.clinical.interfaces import IDomainManager
from avrc.data.store.ext.clinical.interfaces import IProtocol
from avrc.data.store.ext.clinical.interfaces import IProtocolManager

from avrc.data.store.ext.clinical import model



class Subject(Item):
    """ See `ISubject`
    """
    implements(ISubject)

    zid = FieldProperty(ISubject['zid'])
    uid = FieldProperty(ISubject['uid'])
    nurse_email = FieldProperty(ISubject['nurse_email'])
    aeh = FieldProperty(ISubject['aeh'])
    our = FieldProperty(ISubject['our'])


class Partner(Item):
    """ See `IPartner`
    """
    implements(IPartner)

    zid = FieldProperty(IPartner['zid'])
    subject_zid = FieldProperty(IPartner['subject_zid'])
    enrolled_subject_zid = FieldProperty(IPartner['enrolled_subject_zid'])
    visit_date = FieldProperty(IPartner['visit_date'])


class Enrollment(Item):
    """ See `IEnrollment`
    """
    implements(IEnrollment)

    subject_zid = FieldProperty(IVisit['subject_zid'])
    start_date = FieldProperty(IEnrollment['start_date'])
    consent_date = FieldProperty(IEnrollment['consent_date'])
    stop_date = FieldProperty(IEnrollment['stop_date'])
    eid = FieldProperty(IEnrollment['eid'])


class Visit(Item):
    """ See `IVisit`
    """
    implements(IVisit)

    zid = FieldProperty(IVisit['zid'])
    subject_zid = FieldProperty(IVisit['subject_zid'])
    protocol_zids = FieldProperty(IVisit['protocol_zids'])
    visit_date = FieldProperty(IVisit['visit_date'])


class Domain(Item):
    """ See `IDomain`
    """
    implements(IDomain)

    zid = FieldProperty(IDomain['zid'])
    code = FieldProperty(IDomain['code'])
    title = FieldProperty(IDomain['title'])
    consent_date = FieldProperty(IDomain['consent_date'])


class Protocol(Item):
    """ See `IProtocol`
    """
    implements(IProtocol)

    zid = FieldProperty(IProtocol['zid'])
    cycle = FieldProperty(IProtocol['cycle'])
    domain_zid = FieldProperty(IProtocol['domain_zid'])
    threshold = FieldProperty(IProtocol['threshold'])
    is_active = FieldProperty(IProtocol['is_active'])


class SubjectManager(EAVContainerManager):
    classProvides(IDataStoreExtension)
    adapts(IDataStore)
    implements(ISubjectManager)


    _model = model.Subject
    _type = Subject

    def putProperties(self, rslt, source):
        """ Add the items from the source to ds """
        rslt.zid = source.zid
        rslt.uid = source.uid
        rslt.nurse_email = source.nurse_email
        rslt.aeh = source.aeh
        rslt.our = source.our


class PartnerManager(EAVContainerManager):
    """ See `IPartnerManager`
    """
    classProvides(IDataStoreExtension)
    adapts(IDataStore)
    implements(IPartnerManager)


    _model = model.Partner
    _type = Partner

    def putProperties(self, rslt, source):
        Session = self.datastore.session
        subject = Session.query(model.Subject)\
            .filter_by(zid=source.subject_zid)\
            .first()

        enrolled_subject = Session.query(model.Subject)\
            .filter_by(zid=source.enrolled_subject_zid)\
            .first()

        rslt.zid = source.zid
        rslt.subject = subject
        rslt.enrollment_subject = enrolled_subject
        rslt.visit_date = source.visit_date


class EnrollmentManager(EAVContainerManager):
    classProvides(IDataStoreExtension)
    adapts(IDataStore)
    implements(IEnrollmentManager)


    _model = model.Enrollment
    _type = Enrollment

    def putProperties(self, rslt, source):
        """ Add the items from the source to ds """
        Session = self.datastore.session

        domain = Session.query(model.Domain)\
                      .filter_by(zid=source.domain_zid)\
                      .first()

        subject = Session.query(model.Subject)\
                      .filter_by(zid=source.subject_zid)\
                      .first()

        rslt.subject = subject
        rslt.domain = domain
        rslt.start_date = source.start_date
        rslt.consent_date = source.consent_date
        rslt.stop_date = source.stop_date
        rslt.eid = getattr(source, 'eid', None)


    def get_objects_by_eid(self, eid, iface=None):
        """ Utility method for retrieving objects based on the enrollment and
            (optionally) based on when it was collected.
        """
        Session = self.datastore.session

        search_q = Session.query(model.Instance.id) \
            .select_from(orm.join(model.Visit, model.Instance, 'instances'))\
            .join(model.Visit.subject) \
            .join(model.Enrollment) \
            .filter(model.Enrollment.eid == unicode(eid)) \
            .filter(model.Visit.visit_date >= model.Enrollment.start_date) \
            .filter(sa.or_(
                model.Enrollment.stop_date == None,
                model.Visit.visit_date <= model.Enrollment.stop_date
                ))

        if iface is not None:
            iface_name = ''
            iface_version = None

            if isinstance(iface, basestring):
                if len(iface):
                    iface_name = unicode(iface)
                else:
                    raise Exception('Empty schema name specified for search')
            elif iface.extends(Schema):
                iface_name = iface.__name__
                iface_version = iface.__version__
            else:
                raise Exception('Invalid schema for search: %s' % iface)

            search_q = search_q.join(model.Schema)\
                        .join(model.Specification)\
                        .filter(model.Specification.name == iface_name)

            if iface_version:
                exp_q = model.Schema.create_date == iface_version
                search_q = search_q.filter(exp_q)

        return [self.datastore.get(name) for (name,) in search_q.all()]


class VisitManager(EAVContainerManager):
    classProvides(IDataStoreExtension)
    adapts(IDataStore)
    implements(IVisitManager)


    _model = model.Visit
    _type = Visit

    def putProperties(self, rslt, source):
        """ Add the items from the source to ds """
        Session = self.datastore.session

        subject = Session.query(model.Subject)\
          .filter_by(zid=source.subject_zid)\
          .first()

        rslt.zid = source.zid
        rslt.subject = subject
        rslt.visit_date = source.visit_date

        for protocol_zid in source.protocol_zids:
            rslt.protocols.append(Session.query(model.Protocol)\
                .filter_by(zid=protocol_zid)\
                .first())


class DomainManager(ConventionalManager):
    classProvides(IDataStoreExtension)
    adapts(IDataStore)
    implements(IDomainManager)


    _model = model.Domain
    _type = Domain

    def putProperties(self, rslt, source):
        """ Add the items from the source to ds """
        rslt.zid = source.zid
        rslt.title = source.title
        rslt.code = source.code
        rslt.consent_date = source.consent_date
        return rslt


class ProtocolManager(ConventionalManager):
    classProvides(IDataStoreExtension)
    adapts(IDataStore)
    implements(IProtocolManager)

    _model = model.Protocol
    _type = Protocol

    def putProperties(self, rslt, source):
        """ Add the items from the source to ds """
        session = self.datastore.session
        domain = session.query(model.Domain)\
            .filter_by(zid=source.domain_zid)\
            .first()
        rslt.zid = source.zid
        rslt.domain = domain
        rslt.cycle = source.cycle
        rslt.threshold = source.threshold
        rslt.is_active = source.is_active
        return rslt
