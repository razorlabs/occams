import unittest2 as unittest
import datetime

from zope import interface

from occams.datastore import model

from occams.form import interfaces
from occams.form import testing
from occams.form import traversal
from occams.form.browser import editor


class VariableNameValidatorTestCase(unittest.TestCase):

    layer = testing.OCCAMS_FORM_INTEGRATION_TESTING

    def test_invalid_name_space(self):
        u"""
        A form field name cannot contain spaces
        """
        field = interfaces.IEditableField['name']
        validator = editor.VariableNameValidator(None, None, None, field, None)
        with self.assertRaises(interface.Invalid):
            validator.validate('my field')

    def test_invalid_name_dash(self):
        u"""
        A form field name cannot contain dashes
        """
        field = interfaces.IEditableField['name']
        validator = editor.VariableNameValidator(None, None, None, field, None)
        with self.assertRaises(interface.Invalid):
            validator.validate('my-field')

