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


_ = MessageFactory(__name__)

class Domain(object):
    implements(interfaces.IDomain)

    __doc__ = interfaces.IDomain.__doc__

    code = FieldProperty(interfaces.IDomain["code"])

    title = FieldProperty(interfaces.IDomain["title"])

    consent_date = FieldProperty(interfaces.IDomain["consent_date"])

    def __init__(self, code, title, consent_date):
        self.code = code
        self.title = title
        self.consent_date = consent_date

DomainFactory = Factory(
    Domain,
    title=_(u"Create a domain instance"),
    )

class DatastoreDomainManager(object):
    adapts(interfaces.IDatastore)
    implements(interfaces.IDomainManager)

    __doc__ = interfaces.IDomainManager.__doc__

    def __init__(self, datastore):
        self._datastore = datastore

    def has(self, key):
        pass

    has.__doc__ = interfaces.IDomainManager["has"].__doc__

    def get(self, key):
        Session = named_session(self._datastore)
        session = Session()

        domain_rslt = session.query(model.Domain)\
                      .filter_by(title=key)\
                      .first()

        return Domain(title=domain_rslt.title)

    get.__doc__ = interfaces.IDomainManager["get"].__doc__

    def put(self, source):
        Session = named_session(self._datastore)
        session = Session()

        domain_rslt = session.query(model.Domain)\
                      .filter_by(title=source.title)\
                      .first()

        if domain_rslt is None:
            domain_rslt = model.Domain()
            session.add(domain_rslt)

        # won't update the code
        domain_rslt.title = source.title
        session.commit()

    put.__doc__ = interfaces.IDomainManager["put"].__doc__

    def retire(self, source):
        pass

    retire.__doc__ = interfaces.IDomainManager["retire"].__doc__

    def restore(self, key):
        pass

    restore.__doc__ = interfaces.IDomainManager["restore"].__doc__

    def purge(self, source):
        Session = getUtility(interfaces.ISessionFactory)()
        rslt = Session.query(model.Domain).filter_by(title=source.title)
        if rslt is not None:
            Session.remove(rslt)
        Session.commit()

    purge.__doc__ = interfaces.IDomainManager["purge"].__doc__

    def keys(self):
        listing = []
        Session = getUtility(interfaces.ISessionFactory)()

        for rslt in Session.query(model.Domain).all():
            listing.append(Domain(title=rslt.title))

        return listing

    keys.__doc__ = interfaces.IDomainManager["keys"].__doc__
