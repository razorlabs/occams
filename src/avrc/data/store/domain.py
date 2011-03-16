""" Contains how to: domain and protocol
"""
from zope.component import adapts

from zope.schema.fieldproperty import FieldProperty
from zope.interface import implements

from avrc.data.store import MessageFactory as _
from avrc.data.store.interfaces import IDatastore
from avrc.data.store.interfaces import IDomain
from avrc.data.store.interfaces import IDomainManager
from avrc.data.store.interfaces import IProtocol
from avrc.data.store.interfaces import IProtocolManager
from avrc.data.store import model
from avrc.data.store._item import AbstractItem
from avrc.data.store._manager import AbstractDatastoreConventionalManager


class Domain(AbstractItem):
    """ See `IDomain`
    """
    implements(IDomain)

    zid = FieldProperty(IDomain['zid'])
    code = FieldProperty(IDomain['code'])
    title = FieldProperty(IDomain['title'])
    consent_date = FieldProperty(IDomain['consent_date'])


class Protocol(AbstractItem):
    """ See `IProtocol`
    """
    implements(IProtocol)

    zid = FieldProperty(IProtocol['zid'])
    cycle = FieldProperty(IProtocol['cycle'])
    domain_zid = FieldProperty(IProtocol['domain_zid'])
    threshold = FieldProperty(IProtocol['threshold'])
    is_active = FieldProperty(IProtocol['is_active'])


class DatastoreDomainManager(AbstractDatastoreConventionalManager):
    adapts(IDatastore)
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


class DatastoreProtocolManager(AbstractDatastoreConventionalManager):
    adapts(IDatastore)
    implements(IProtocolManager)

    _model = model.Protocol
    _type = Protocol

    def putProperties(self, rslt, source):
        """ Add the items from the source to ds """
        Session = self._datastore.getScopedSession()

        domain = Session.query(model.Domain)\
            .filter_by(zid=source.domain_zid)\
            .first()

        rslt.zid = source.zid
        rslt.domain = domain
        rslt.cycle = source.cycle
        rslt.threshold = source.threshold
        rslt.is_active = source.is_active
