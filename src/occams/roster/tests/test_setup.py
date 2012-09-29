import unittest2 as unittest

from Products.CMFCore.utils import getToolByName

from occams.roster import testing
from occams.roster import model
from occams.roster import interfaces
from occams.roster import Session


class SetupTestCase(unittest.TestCase):
    u"""
    Ensures application can be properly installed
    """

    layer = testing.OCCAMS_ROSTER_INTEGRATION_TESTING

    def testRosterInstalled(self):
        portal = self.layer[u'portal']
        quickinstaller = getToolByName(portal, u'portal_quickinstaller')
        self.assertTrue(quickinstaller.isProductInstalled(u'occams.roster'))


class DatabaseConfigurationTestCase(unittest.TestCase):
    u"""
    Ensures the database is properly configured
    """

    layer = testing.OCCAMS_ROSTER_INTEGRATION_TESTING

    def test_starting_point(self):
        u"""
        Ensure that the OUR numbers can be generated at the correct starting id
        """
        session = Session()
        identifier = model.Identifier(origin=model.Site(title=u'Foo'))
        session.add(identifier)
        session.flush()

        self.assertGreaterEqual(identifier.id, interfaces.START_ID,
            msg=u'OUR number id starting point not installed correctly'
            )

