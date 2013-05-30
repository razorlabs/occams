import unittest2 as unittest

from Products.CMFCore.utils import getToolByName

from occams.form import testing


class SetupTestCase(unittest.TestCase):

    layer = testing.OCCAMS_FORM_INTEGRATION_TESTING

    def assert_installed(self, namespace):
        portal = self.layer['portal']
        quickinstaller = getToolByName(portal, 'portal_quickinstaller')
        is_installed = quickinstaller.isProductInstalled(namespace)
        if not is_installed:
            self.fail('[%s] was not installed!' % namespace)

    def test_installed(self):
        self.assert_installed('occams.form')

    def test_dexterity_installed(self):
        self.assert_installed('plone.app.dexterity')

    def test_jquery_tools_installed(self):
        self.assert_installed('plone.app.jquerytools')

    def test_z3c_form_installed(self):
        self.assert_installed('plone.app.z3cform')

    def test_datagrid_field_installed(self):
        self.assert_installed('collective.z3cform.datagridfield')

    def test_saconnect_installed(self):
        self.assert_installed('collective.saconnect')