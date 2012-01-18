import unittest2 as unittest
from Products.CMFCore.utils import getToolByName

from occams.form.testing import OCCAMS_FORM_INTEGRATION_TESTING


class TestSetup(unittest.TestCase):

    layer = OCCAMS_FORM_INTEGRATION_TESTING

    def assertInstalled(self, namespace):
        portal = self.layer['portal']
        quickinstaller = getToolByName(portal, 'portal_quickinstaller')
        isInstalled = quickinstaller.isProductInstalled(namespace)
        if not isInstalled:
            self.fail('[%s] was not installed!' % namespace)

    def testInstalled(self):
        self.assertInstalled('occams.form')

    def testDexterityInstalled(self):
        self.assertInstalled('plone.app.dexterity')

    def testJqueryToolsInstalled(self):
        self.assertInstalled('plone.app.jquerytools')

    def testZ3cFormInstalled(self):
        self.assertInstalled('plone.app.z3cform')

    def testDatagridFieldInstalled(self):
        self.assertInstalled('collective.z3cform.datagridfield')

