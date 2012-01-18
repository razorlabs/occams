import unittest2 as unittest

from Products.CMFCore.utils import getToolByName

from occams.form.testing import OCCAMS_FORM_INTEGRATION_TESTING


class TestForm(unittest.TestCase):

    layer = OCCAMS_FORM_INTEGRATION_TESTING


