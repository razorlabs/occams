
import datetime
import unittest2 as unittest

from zope.interface.interface import InterfaceClass
import zope.schema
from zope.schema.interfaces import WrongType
from zope.schema.interfaces import ConstraintNotSatisfied

from avrc.data.store import directives
from avrc.data.store import model


class SchemaOrFieldDirectivesTestCase(unittest.TestCase):
    """ 
    Verifies directive library
    """

    def test_id (self):
        iface = InterfaceClass('Sample')
        field = zope.schema.Text(__name__='foo', title=u'Foo')
        directive = directives.__id__
        self.assertRaises(WrongType, directive.set, iface, 'This is an id')
        self.assertRaises(WrongType, directive.set, iface, 12.4)

        value = 1234
        directive.set(iface, value)
        self.assertEqual(value, directive.bind().get(iface))
        directive.set(field, value)
        self.assertEqual(value, directive.bind().get(field))



    def test_version (self):
        iface = InterfaceClass('Sample')
        field = zope.schema.Text(__name__='foo', title=u'Foo')
        directive = directives.version
        self.assertRaises(WrongType, directive.set, iface, 'This is an id')
        self.assertRaises(WrongType, directive.set, iface, 12.4)
        self.assertRaises(WrongType, directive.set, iface, 1234)

        value = datetime.datetime.now()
        directive.set(iface, value)
        self.assertEqual(value, directive.bind().get(iface))
        directive.set(field, value)
        self.assertEqual(value, directive.bind().get(field))


    def test_inline (self):
        iface = InterfaceClass('Sample')
        field = zope.schema.Text(__name__='foo', title=u'Foo')
        directive = directives.inline
        self.assertRaises(WrongType, directive.set, iface, 'This is an id')
        self.assertRaises(WrongType, directive.set, iface, 12.4)

        value = True
        directive.set(iface, value)
        self.assertEqual(value, directive.bind().get(iface))
        directive.set(field, value)
        self.assertEqual(value, directive.bind().get(field))


class SchemaDirectivesTestCase(unittest.TestCase):


    def test_title(self):
        iface = InterfaceClass('Sample')
        directive = directives.title
        self.assertRaises(WrongType, directive.set, iface, 1234)
        self.assertRaises(WrongType, directive.set, iface, 'This is \n a title')

        value = u'This is a title'
        directive.set(iface, value)
        self.assertEqual(value, directive.bind().get(iface))


    def test_description(self):
        iface = InterfaceClass('Sample')
        directive = directives.description
        self.assertRaises(WrongType, directive.set, iface, 1234)

        value = u'This is a title'
        directive.set(iface, value)
        self.assertEqual(value, directive.bind().get(iface))


class FieldDirectivesTestCase(unittest.TestCase):

    def test_type (self):
        field = zope.schema.Choice(__name__='foo', title=u'Foo', values=[1, 2, 3])
        directive = directives.type

        # Check all supported
        for type_ in model.Attribute.__table__.c.type.type.enums:
            if type_ not in directives.CASTS:
                exception = ConstraintNotSatisfied
                self.assertRaises(exception, directive.set, field, type_)
            else:
                directive.set(field, type_)

        value = 'string'
        directive.set(field, value)
        self.assertEqual(value, directive.bind().get(field))


    def test_widget (self):
        field = zope.schema.TextLine(__name__='foo', title=u'Foo')
        directive = directives.widget

        # Check all supported
        value = 'avrc.data.store.NonExistentWidget'
        directive.set(field, value)
        self.assertEqual(value, directive.bind().get(field))
