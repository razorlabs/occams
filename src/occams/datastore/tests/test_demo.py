
from datetime import date
import unittest2 as unittest

from zope.interface.interface import InterfaceClass
import zope.schema

from occams.datastore.testing import DATABASE_LAYER
from occams.datastore import directives
from occams.datastore import model
from occams.datastore.schema import SchemaManager
from occams.datastore.schema import FieldManager
from occams.datastore.storage import ObjectFactory
from occams.datastore.storage import EntityManager
from occams.datastore.storage import ValueManager


class DemoTestCase(unittest.TestCase):
    """
    A real-world usage case scenario
    """

    layer = DATABASE_LAYER

    def test_demo(self):
        session = self.layer['session']

        ### 1. First we need a schema

        OriginalSampleSchema = InterfaceClass('Sample', bases=[directives.Schema])
        directives.title.set(OriginalSampleSchema, u'Sample Schema')

        schemata = SchemaManager(session)
        id = schemata.put(OriginalSampleSchema.__name__, OriginalSampleSchema)

        ### 2. Now add fields to it

        schema = session.query(model.Schema).get(id)
        fields = FieldManager(schema)
        foo = zope.schema.TextLine(__name__='foo', title=u'Foo')
        fields.put(foo.__name__, foo)

        ### 3. Now add instances

        # A reload is always required after a schema change
        SampleSchema = schemata.get('Sample')
        sample = ObjectFactory(SampleSchema)
        entities = EntityManager(session)
        id = entities.put(None, sample)

        # Ensure that the collect date was automatically set since we didn't
        # specify one
        self.assertEqual(sample.getCollectDate(), sample.__version__.date())

        ### 4. Now assign values

        entity = session.query(model.Entity).get(id)
        values = ValueManager(entity)
        values.put('foo', u'This is Foo. 1')
        values.put('foo', u'This is Foo. 2')
        values.put('foo', u'This is Foo. 3')

        ### 5. Change the schema fields

        foo = zope.schema.TextLine(
            __name__='foo',
            title=u'Foo',
            description=u'This needs a foo',
            )

        fields.put(foo.__name__, foo)
        SampleSchema = schemata.get('Sample')

        ### 7. Now add more values

        entities = EntityManager(session)
        sample = ObjectFactory(SampleSchema)
        id = entities.put(None, sample)

        ### 8. Now assign values

        entity = session.query(model.Entity).get(id)
        values = ValueManager(entity)
        values.put('foo', u'This is Foo. 4')
        values.put('foo', u'This is Foo. 5')
