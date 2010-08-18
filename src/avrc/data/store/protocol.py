"""
Contains how to: domain and protocol
"""
from zope.component import adapts
from zope.component import getUtility
from zope.component.factory import Factory
from zope.interface import implements
from zope.i18nmessageid import MessageFactory

from avrc.data.store import interfaces
from avrc.data.store import model

_ = MessageFactory(__name__)

#class Domain(object):
#    """
#    """
#    implements(interfaces.IDomain)
#
#    title = None
#
#    def to_db(self):
#        pass
#
#    @classmethod
#    def from_db(cls, rslt):
#        obj = cls()
#        return obj
#
#DomainFactory = Factory(
#    Domain,
#    title=_(u"Create a new domain"),
#    description=_("New domain generator")
#    )

class ProtocolManager(object):
    pass

class DatastoreDomainManager(object):
    """
    """
    adapts(interfaces.IDatastore)
    implements(interfaces.IDomainManager)

    def __init__(self, engine):
        self.datastore = engine

    def get(self, key):
        """
        """
        Session = getUtility(interfaces.ISessionFactory)()

        domain_rslt = Session.query(model.Domain)\
                      .filter_by(title=key)\
                      .first()

        return Domain.copy(domain_rslt)

    def add(self, source):
        """
        """
        Session = getUtility(interfaces.ISessionFactory)()
        Session.add( model.Domain(title=source.title) )
        Session.commit()

    def modify(self, old, new):
        """
        """
        Session = getUtility(interfaces.ISessionFactory)()
        rslt = Session.query(model.Domain).filter_by(title=old.title).first()
        rslt.title = new.title
        Session.commit()

    def expire(self, source):
        """
        """
        raise NotImplementedError()

    def remove(self, source):
        """
        """
        Session = getUtility(interfaces.ISessionFactory)()
        rslt = Session.query(model.Domain).filter_by(title=source.title)
        if rslt is not None:
            Session.remove(rslt)
        Session.commit()

    def list(self):
        """
        """
        listing = []
        Session = getUtility(interfaces.ISessionFactory)()

        for rslt in Session.query(model.Domain).all():
            listing.append(Domain(title=rslt.title))

        return listing

