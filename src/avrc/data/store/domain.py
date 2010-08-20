"""
Contains how to: domain and protocol
"""
from zope.component import adapts
from zope.component import getUtility
from zope.schema.fieldproperty import FieldProperty
from zope.component.factory import Factory
from zope.interface import implements
from zope.i18nmessageid import MessageFactory

from avrc.data.store import interfaces
from avrc.data.store import model
from avrc.data.store.datastore import named_session
from avrc.data.store._utils import DatastoreConventionalManager

_ = MessageFactory(__name__)

class Domain(object):
    implements(interfaces.IDomain)

    __doc__ = interfaces.IDomain.__doc__

    code = FieldProperty(interfaces.IDomain["code"])

    title = FieldProperty(interfaces.IDomain["title"])

    consent_date = FieldProperty(interfaces.IDomain["consent_date"])

    schemata = FieldProperty(interfaces.IDomain["schemata"])

    def __init__(self, code, title, consent_date):
        self.code = code
        self.title = title
        self.consent_date = consent_date

DomainFactory = Factory(
    Domain,
    title=_(u"Create a domain instance"),
    )

class DatastoreDomainManager(DatastoreConventionalManager):
    adapts(interfaces.IDatastore)
    implements(interfaces.IDomainManager)

    __doc__ = interfaces.IDomainManager.__doc__

    def __init__(self, datastore):
        self._datastore = datastore
        self._model = model.Domain
        self._type = Domain

    def putProperties(self, rslt, source):
        """
        Add the items from the source to ds
        """
        rslt.zid = source.zid
        rslt.title = source.title 
        rslt.code = source.code
        rslt.consent_date = source.consent_date
        return rslt
    
class Protocol(object):
    implements(interfaces.IProtocol)

    __doc__ = interfaces.IProtocol.__doc__

    cycle = FieldProperty(interfaces.IProtocol["cycle"])

    domain_title = FieldProperty(interfaces.IProtocol["domain_title"])
    
    threshold = FieldProperty(interfaces.IProtocol["threshold"])

    is_active = FieldProperty(interfaces.IProtocol["is_active"])

    def __init__(self, cycle, domain_title, threshold=None, is_active=True):
        self.cycle = cycle
        self.domain_title = domain_title
        self.threshold = threshold
        self.is_active = is_active

ProtocolFactory = Factory(
    Protocol,
    title=_(u"Create a protocol instance"),
    )

class DatastoreProtocolManager(DatastoreConventionalManager):
    adapts(interfaces.IDatastore)
    implements(interfaces.IProtocolManager)

    __doc__ = interfaces.IProtocolManager.__doc__

    def __init__(self, datastore):
        self._datastore = datastore
        self._model = model.Protocol
        self._type = Protocol

    def put(self, source):
        Session = named_session(self._datastore)
        session = Session()
        is_new = False

        rslt = session.query(self._model)\
                      .filter_by(zid=source.zid)\
                      .first()

        domain = session.query(model.Domain)\
                      .filter_by(zid=source.domain_zid)\
                      .first()
        if rslt is None:
            rslt = self._model(domain=domain, zid=source.zid, cycle=source.cycle, threshold=source.threshold, is_active=source.is_active)
            session.add(rslt)
        else:
        # won't update the code
            rslt = self.putProperties(rslt, source, session)
        domain_rslt.consent_date = source.consent_date

        if is_new:
            session.add(domain_rslt)

        session.commit()

    def putProperties(self, rslt, source):
        """
        Add the items from the source to ds
        """
        rslt.cycle = source.cycle
#        rslt.schemata.append(;lasdkfjas;lfj;saldfja;sldjfsa;ldjf;saldfjsa;fhsa)
        rslt.threshold = source.threshold
        rslt.is_active = source.is_active
        return rslt
    