import unittest2 as unittest
from Products.CMFCore.utils import getToolByName

from hive.form.testing import HIVE_FORM_INTEGRATION_TESTING


class TestSetup(unittest.TestCase):

    layer = HIVE_FORM_INTEGRATION_TESTING

    def test_installed(self):
        portal = self.layer['portal']
        quickinstaller = getToolByName(portal, 'portal_quickinstaller')
        self.assertTrue(quickinstaller.isProductInstalled('hive.form'))
