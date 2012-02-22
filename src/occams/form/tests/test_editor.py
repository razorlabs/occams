import unittest2 as unittest

import zope.interface

from occams.form.testing import OCCAMS_FORM_INTEGRATION_TESTING
from occams.form.browser.editor import VariableNameValidator
from occams.form.traversal import SchemaContext
from occams.form.traversal import AttributeContext
from occams.form.interfaces import IEditableField


class TestFieldDelete(unittest.TestCase):

    layer = OCCAMS_FORM_INTEGRATION_TESTING

    def testFieldFromForm(self):
        self.fail()

    def testFieldFromFieldset(self):
        self.fail()

    def testFieldsetFromForm(self):
        self.fail()


class TestFieldEdit(unittest.TestCase):

    layer = OCCAMS_FORM_INTEGRATION_TESTING


class TestFieldOrder(unittest.TestCase):

    layer = OCCAMS_FORM_INTEGRATION_TESTING


class TestFieldAdd(unittest.TestCase):

    layer = OCCAMS_FORM_INTEGRATION_TESTING

    def assertNotValidName(self, validator, name):
        with self.assertRaises(zope.interface.Invalid,
                msg='Expected invalid variable name'):
            validator.validate(name)

    def assertValidName(self, validator, name):
        validator.validate(name)

    def testVariableName(self):
        """
        Test that we can add valid variables to a form
        """
        field = IEditableField['name']
        context = SchemaContext(data=dict(
            name='Foo',
            title=u'Foo',
            fields=dict.fromkeys(('foo', 'bar', 'baz'))
            ))

        validator = VariableNameValidator(context, None, None, field, None)

        # Can't add invalid variable names
        self.assertNotValidName(validator, '----')
        self.assertNotValidName(validator, 'foo-bar')
        self.assertNotValidName(validator, 'foo bar')

        # Can't add variable names that already exist
        self.assertNotValidName(validator, 'foo')
        self.assertValidName(validator, 'jaz')

        context = AttributeContext(data=dict(
            name='Foo',
            title=u'Foo',
            schema=dict(
                name='SubFoo',
                title=u'Sub Foo',
                fields=dict.fromkeys(('foo', 'bar', 'baz'))
                )
            ))

        validator = VariableNameValidator(context, None, None, field, None)

        # Can't add invalid variable names
        self.assertNotValidName(validator, '----')
        self.assertNotValidName(validator, 'foo-bar')
        self.assertNotValidName(validator, 'foo bar')

        # Can't add variable names that already exist
        self.assertNotValidName(validator, 'foo')
        self.assertValidName(validator, 'jaz')
