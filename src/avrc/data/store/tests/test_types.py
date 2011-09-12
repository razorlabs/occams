
import unittest2 as unittest
import decimal
import datetime

from avrc.data.store import model
from avrc.data.store.storage import ValueManager
from avrc.data.store.storage import ObjectFactory
from avrc.data.store.schema import SchemaManager

from avrc.data.store.testing import DATABASE_LAYER


class TypeTestCase(unittest.TestCase):
    """ 
    Verifies all value types can be used properly (as well as their choice
    counterparts).
    """

    layer = DATABASE_LAYER


    def setUp(self):
        session = self.session = self.layer['session']
        self.schema = model.Schema(name='Sample', title=u'Sample Schema')
        self.entity = model.Entity(schema=self.schema, name='foobar', title=u'FooBar')
        session.add(self.entity)
        self.manager = ValueManager(self.entity)


    def tearDown(self):
        self.manager = None


    def test_boolean(self):
        session = self.manager.session
        manager = self.manager
        name = 'foo'
        attribute = model.Attribute(
            type='boolean',
            schema=self.schema,
            name=name,
            title=u'Not important.',
            order=1
            )
        session.add(attribute)
        session.flush()

        value = True
        id = manager.put(name, value)
        result = manager.get(name)
        self.assertTrue(isinstance(result, bool))
        self.assertEqual(value, result)

        value = False
        id = manager.put(name, value)
        result = manager.get(name)
        self.assertTrue(isinstance(result, bool))
        self.assertEqual(value, result)


    def test_boolean_choice(self):
        session = self.manager.session
        manager = self.manager
        name = 'foo'
        attribute = model.Attribute(
            type='boolean',
            schema=self.schema,
            name=name,
            title=u'Not important.',
            order=1,
            choices=dict(
                no=model.Choice(name='no', title=u'No', value=unicode(False), order=1),
                yes=model.Choice(name='yes', title=u'Yes', value=unicode(True), order=2),
                )
            )
        session.add(attribute)
        session.flush()
        value = True
        id = manager.put(name, value)
        result = manager.get(name)
        self.assertEqual(value, result)
        entry = session.query(model.ValueInteger).get(id)
        self.assertEqual(entry.choice.name, 'yes')

        value = False
        id = manager.put(name, value)
        result = manager.get(name)
        self.assertTrue(isinstance(result, bool))
        self.assertEqual(value, result)
        entry = session.query(model.ValueInteger).get(id)
        self.assertEqual(entry.choice.name, 'no')


    def test_integer(self):
        session = self.manager.session
        manager = self.manager
        name = 'foo'
        attribute = model.Attribute(
            type='integer',
            schema=self.schema,
            name=name,
            title=u'Not important.',
            order=1
            )
        session.add(attribute)
        session.flush()

        value = 420
        id = manager.put(name, value)
        result = manager.get(name)
        self.assertTrue(isinstance(result, int))
        self.assertEqual(value, result)



    def test_integer_choice(self):
        session = self.manager.session
        manager = self.manager
        name = 'foo'
        attribute = model.Attribute(
            type='integer',
            schema=self.schema,
            name=name,
            title=u'Not important.',
            order=1,
            choices=dict(
                bad=model.Choice(name='bad', title=u'Bad', value=0, order=1),
                ok=model.Choice(name='ok', title=u'Ok', value=1, order=2),
                good=model.Choice(name='good', title=u'Good', value=2, order=3),
                )
            )
        session.add(attribute)
        session.flush()

        value = 2
        id = manager.put(name, value)
        result = manager.get(name)
        self.assertTrue(isinstance(result, int))
        self.assertEqual(value, result)
        entry = session.query(model.ValueInteger).get(id)
        self.assertEqual(entry.choice.name, 'good')


    def test_string(self):
        session = self.manager.session
        manager = self.manager
        name = 'foo'
        attribute = model.Attribute(
            type='string',
            schema=self.schema,
            name=name,
            title=u'Not important.',
            order=1
            )
        session.add(attribute)
        session.flush()

        value = u'FOO!!!!!'
        id = manager.put(name, value)
        result = manager.get(name)
        self.assertTrue(isinstance(result, unicode))
        self.assertEqual(value, result)


    def test_string_choice(self):
        session = self.manager.session
        manager = self.manager
        name = 'foo'
        attribute = model.Attribute(
            type='text',
            schema=self.schema,
            name=name,
            title=u'Not important.',
            order=1,
            choices=dict(
                bad=model.Choice(name='bad', title=u'Bad', value=u'bad', order=1),
                ok=model.Choice(name='ok', title=u'Ok', value=u'ok', order=2),
                good=model.Choice(name='good', title=u'Good', value=u'good', order=3),
                )
            )
        session.add(attribute)
        session.flush()

        value = u'ok'
        id = manager.put(name, value)
        result = manager.get(name)
        self.assertTrue(isinstance(result, unicode))
        self.assertEqual(value, result)
        entry = session.query(model.ValueString).get(id)
        self.assertEqual(entry.choice.name, 'ok')


    def test_text(self):
        session = self.manager.session
        manager = self.manager
        name = 'foo'
        attribute = model.Attribute(
            type='text',
            schema=self.schema,
            name=name,
            title=u'Not important.',
            order=1
            )
        session.add(attribute)
        session.flush()

        value = u"""
        This is only a
        test
        """
        id = manager.put(name, value)
        result = manager.get(name)
        self.assertTrue(isinstance(result, unicode))
        self.assertEqual(value, result)


    def test_text_choice(self):
        session = self.manager.session
        manager = self.manager
        name = 'foo'
        attribute = model.Attribute(
            type='text',
            schema=self.schema,
            name=name,
            title=u'Not important.',
            order=1,
            choices=dict(
                bad=model.Choice(name='bad', title=u'Bad', value=u'bad\n', order=1),
                ok=model.Choice(name='ok', title=u'Ok', value=u'ok\n', order=2),
                good=model.Choice(name='good', title=u'Good', value=u'good\n', order=3),
                )
            )
        session.add(attribute)
        session.flush()
        value = u'bad\n'
        id = manager.put(name, value)
        result = manager.get(name)
        self.assertTrue(isinstance(result, unicode))
        self.assertEqual(value, result)
        entry = session.query(model.ValueString).get(id)
        self.assertEqual(entry.choice.name, 'bad')


    def test_decimal(self):
        session = self.manager.session
        manager = self.manager
        name = 'foo'
        attribute = model.Attribute(
            type='decimal',
            schema=self.schema,
            name=name,
            title=u'Not important.',
            order=1
            )
        session.add(attribute)
        session.flush()

        value = decimal.Decimal('4.20')
        id = manager.put(name, value)
        result = manager.get(name)
        self.assertTrue(isinstance(result, decimal.Decimal))
        self.assertEqual(value, result)


    def test_decimal_choice(self):
        session = self.manager.session
        manager = self.manager
        name = 'foo'
        attribute = model.Attribute(
            type='decimal',
            schema=self.schema,
            name=name,
            title=u'Not important.',
            order=1,
            choices=dict(
                rarely=model.Choice(name='rarely', title=u'Rarely', value=decimal.Decimal('0.25'), order=1),
                seldom=model.Choice(name='seldom', title=u'Seldom', value=decimal.Decimal('0.50'), order=2),
                always=model.Choice(name='always', title=u'Always', value=decimal.Decimal('0.75'), order=3),
                )
            )
        session.add(attribute)
        session.flush()

        value = decimal.Decimal('0.75')
        id = manager.put(name, value)
        result = manager.get(name)
        self.assertTrue(isinstance(result, decimal.Decimal))
        self.assertEqual(value, result)
        entry = session.query(model.ValueDecimal).get(id)
        self.assertEqual(entry.choice.name, 'always')


    def test_date(self):
        session = self.manager.session
        manager = self.manager
        name = 'foo'
        attribute = model.Attribute(
            type='date',
            schema=self.schema,
            name=name,
            title=u'Not important.',
            order=1
            )
        session.add(attribute)
        session.flush()

        value = datetime.date(1776, 7, 4)
        id = manager.put(name, value)
        result = manager.get(name)
        self.assertTrue(isinstance(result, datetime.date))
        self.assertEqual(value, result)


    def test_date_choice(self):
        session = self.manager.session
        manager = self.manager
        name = 'foo'
        attribute = model.Attribute(
            type='date',
            schema=self.schema,
            name=name,
            title=u'Not important.',
            order=1,
            choices=dict(
                chrismas=model.Choice(name='chrismas', title=u'Chrismas', value=datetime.date(2011, 12, 24), order=1),
                halloween=model.Choice(name='halloween', title=u'Halloween', value=datetime.date(2011, 10, 31), order=2),
                thanksgiving=model.Choice(name='thanksgiving', title=u'Thanksgiving', value=datetime.date(2011, 11, 24), order=3),
                )
            )
        session.add(attribute)
        session.flush()

        value = datetime.date(2011, 10, 31)
        id = manager.put(name, value)
        result = manager.get(name)
        self.assertTrue(isinstance(result, datetime.date))
        self.assertEqual(value, result)
        entry = session.query(model.ValueDatetime).get(id)
        self.assertEqual(entry.choice.name, 'halloween')


    def test_datetime(self):
        session = self.manager.session
        manager = self.manager
        name = 'foo'
        attribute = model.Attribute(
            type='datetime',
            schema=self.schema,
            name=name,
            title=u'Not important.',
            order=1
            )
        session.add(attribute)
        session.flush()

        value = datetime.datetime(1997, 8, 29, 2, 19, 0)
        id = manager.put(name, value)
        result = manager.get(name)
        self.assertTrue(isinstance(result, datetime.datetime))
        self.assertEqual(value, result)


    def test_datetime_choice(self):
        session = self.manager.session
        manager = self.manager
        name = 'foo'
        attribute = model.Attribute(
            type='datetime',
            schema=self.schema,
            name=name,
            title=u'Not important.',
            order=1,
            choices=dict(
                original=model.Choice(name='original', title=u'Original', value=datetime.datetime(1997, 8, 29, 2, 19, 0), order=1),
                crappy=model.Choice(name='crappy', title=u'Crappy', value=datetime.datetime(2004, 7, 25, 6, 18, 0), order=2),
                descent=model.Choice(name='descent', title=u'Descent', value=datetime.datetime(2011, 4, 21, 20, 11, 0), order=3),
                )
            )
        session.add(attribute)
        session.flush()

        value = datetime.datetime(2011, 4, 21, 20, 11, 0)
        id = manager.put(name, value)
        result = manager.get(name)
        self.assertTrue(isinstance(result, datetime.datetime))
        self.assertEqual(value, result)
        entry = session.query(model.ValueDatetime).get(id)
        self.assertEqual(entry.choice.name, 'descent')


    def test_object(self):
        # TODO: this test might require a little more thought, as it contains
        # too many moving parts.
        session = self.manager.session
        manager = self.manager
        name = 'foo'
        dummy = model.Schema(name='Dummy', title=u'Dummy Schema')
        attribute = model.Attribute(
            type='object',
            schema=self.schema,
            object_schema=dummy,
            is_inline_object=True,
            name=name,
            title=u'Not important.',
            order=1
            )
        session.add(attribute)
        session.flush()

        schemata = SchemaManager(session)
        iface = schemata.get('Dummy')
        value = ObjectFactory(iface)
        id = manager.put(name, value)
        result = manager.get(name)
        self.assertEqual(value, result)


    def test_object_choice(self):
        pass
        # No object choices in this release
