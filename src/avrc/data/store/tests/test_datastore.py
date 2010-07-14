import unittest

from Products.Five import zcml
from Products.Five import fiveconfigure
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import PloneSite

from zope.app.folder import rootFolder
from zope.app.component.site import SiteManagerContainer, LocalSiteManager
from zope.app.component.site import setSite
from zope.component import getUtility

import avrc.data.store
from avrc.data.store import interfaces

ptc.setupPloneSite()


from zope.interface import implements

class MockDataStore(object):
    implements(interfaces.IDataStore)
    
    __name__ = __parent__ = None
    
    def __init__(self, fia, pii):
        self.fia = fia
        self.pii = pii


class TestCase(ptc.PloneTestCase):
    class layer(PloneSite):
        @classmethod
        def setUp(cls):
            fiveconfigure.debug_mode = True
            zcml.load_config('configure.zcml', avrc.data.store)
            fiveconfigure.debug_mode = False

        @classmethod
        def tearDown(cls):
            pass
        
    def test_multi_site(self):
        
        root = rootFolder()
        
        root[u"site1"] = site1 = SiteManagerContainer()
        root[u"site2"] = site2 = SiteManagerContainer()
        
        site1.setSiteManager(LocalSiteManager(site1))
        site2.setSiteManager(LocalSiteManager(site2))
        
        sm1 = site1.getSiteManager()
        sm2 = site2.getSiteManager()
        
        sm1['datastore'] = MockDataStore(pii=u"sqlite:///ds1pii.db",  fia=u"sqlite:///ds1fia.db")
        sm2['datastore'] = MockDataStore(pii=u"sqlite:///ds2pii.db",  fia=u"sqlite:///ds2fia.db") 
        
        
        from avrc.data.store import interfaces
        from avrc.data.store import model
        
        setSite(site1)
        SessionFactory = getUtility(interfaces.ISessionFactory)
        Session = SessionFactory()
        
        name = model.Name()
        name.first=u"David"
        name.last=u"Mote"
        
        Session.add(name)
        Session.commit()
        
#        setSite(site2)
#        SessionFactory = getUtility(interfaces.ISessionFactory)
#        Session = SessionFactory()
#        
#        name = model.Name()
#        name.first=u"Marco"
#        name.last=u"Martinez"
#        
#        Session.add(name)
#        Session.commit()
        
        self.fail("Not complete")


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
