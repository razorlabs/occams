""" Contains how to: domain and protocol
"""
import transaction
from zope.component import adapts
from zope.schema.fieldproperty import FieldProperty
from zope.interface import implements

from avrc.data.store import MessageFactory as _
from avrc.data.store import interfaces
from avrc.data.store import model
from avrc.data.store._manager import AbstractDatastoreConventionalManager


class Domain(object):
    implements(interfaces.IDomain)

    __doc__ = interfaces.IDomain.__doc__

    zid = FieldProperty(interfaces.IDomain['zid'])

    code = FieldProperty(interfaces.IDomain['code'])

    title = FieldProperty(interfaces.IDomain['title'])

    consent_date = FieldProperty(interfaces.IDomain['consent_date'])

    def __init__(self, code, title, consent_date):
        self.code = code
        self.title = title
        self.consent_date = consent_date


class Protocol(object):
    implements(interfaces.IProtocol)

    __doc__ = interfaces.IProtocol.__doc__

    zid = FieldProperty(interfaces.IProtocol['zid'])

    cycle = FieldProperty(interfaces.IProtocol['cycle'])

    domain_zid = FieldProperty(interfaces.IProtocol['domain_zid'])

    threshold = FieldProperty(interfaces.IProtocol['threshold'])

    is_active = FieldProperty(interfaces.IProtocol['is_active'])

    def __init__(self, cycle, domain_zid, threshold=None, is_active=True):
        self.cycle = cycle
        self.domain_zid = domain_zid
        self.threshold = threshold
        self.is_active = is_active


class DatastoreDomainManager(AbstractDatastoreConventionalManager):
    adapts(interfaces.IDatastore)
    implements(interfaces.IDomainManager)

    _model = model.Domain
    _type = Domain


    def putProperties(self, rslt, source):
        """ Add the items from the source to ds """
        rslt.zid = source.zid
        rslt.title = source.title
        rslt.code = source.code
        rslt.consent_date = source.consent_date
        return rslt


class DatastoreProtocolManager(AbstractDatastoreConventionalManager):
    adapts(interfaces.IDatastore)
    implements(interfaces.IProtocolManager)

    _model = model.Protocol
    _type = Protocol


    def put(self, source):
        Session = self._datastore.getScopedSession()

        rslt = Session.query(self._model)\
            .filter_by(zid=source.zid)\
            .first()

        domain = Session.query(model.Domain)\
            .filter_by(zid=source.domain_zid)\
            .first()

        if rslt is None:
            rslt = self._model(domain=domain, zid=source.zid, cycle=source.cycle, threshold=source.threshold, is_active=source.is_active)
            Session.add(rslt)

        else:
        # won't update the code
            rslt = self.putProperties(rslt, source)

        transaction.commit()

    def putProperties(self, rslt, source):
        """ Add the items from the source to ds """
        rslt.cycle = source.cycle
        rslt.threshold = source.threshold
        rslt.is_active = source.is_active
        return rslt
