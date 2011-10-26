import unittest2 as unittest
from Products.CMFCore.utils import getToolByName

from occams.form.testing import OCCAMS_FORM_INTEGRATION_TESTING


class TestSetup(unittest.TestCase):

    layer = OCCAMS_FORM_INTEGRATION_TESTING

    def test_installed(self):
        portal = self.layer['portal']
        quickinstaller = getToolByName(portal, 'portal_quickinstaller')
        self.assertTrue(quickinstaller.isProductInstalled('occams.form'))

    def test_dexterity_installed(self):
        portal = self.layer['portal']
        quickinstaller = getToolByName(portal, 'portal_quickinstaller')
        self.assertTrue(quickinstaller.isProductInstalled('plone.app.dexterity'))
