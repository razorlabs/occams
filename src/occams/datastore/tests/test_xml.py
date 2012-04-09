# -*- coding: utf-8 -*-

import codecs
import datetime
import tempfile
from StringIO import StringIO
import lxml.etree
from lxml.objectify import E
import unittest2 as unittest

import sqlalchemy.exc
from occams.datastore import model
from occams.datastore.testing import DATASTORE_LAYER
from occams.datastore.xml import exportXml
from occams.datastore.xml import schemaToElement
from occams.datastore.xml import attributeToElement
from occams.datastore.xml import choiceToElement
from occams.datastore.xml import importXml
from occams.datastore.xml import elementToSchema
from occams.datastore.xml import elementToAttribute
from occams.datastore.xml import elementToChoice
from occams.datastore.interfaces import AlreadyExistsError


class XmlTestCase(unittest.TestCase):

    layer = DATASTORE_LAYER

    def testSchemaToXmlViaStream(self):
        schema = model.Schema(
            name='Foo',
            # Test unicode just for kicks
            title=u'F∆å¬˙∂ß∆å∫¬oo',
            storage='eav',
            state='published',
            publish_date=datetime.date(2012, 03, 01)
            )

        # test with an already open stream
        stream = StringIO()
        exportXml(schema, stream)
        content = stream.getvalue()
        stream.close()
        self.assertIsInstance(content, unicode)
        self.assertIn(u'<schema', content)

    def testSchemaToXmlViaFileName(self):
        schema = model.Schema(
            name='Foo',
            # Test unicode just for kicks
            title=u'F∆å¬˙∂ß∆å∫¬oo',
            storage='eav',
            state='published',
            publish_date=datetime.date(2012, 03, 01)
            )

        # test with a temporary filename
        target = tempfile.NamedTemporaryFile(delete=False)
        target.close()
        exportXml(schema, target.name)
        with codecs.open(target.name, encoding='utf-8') as stream:
            content = stream.read()
        self.assertIsInstance(content, unicode)
        self.assertIn(u'<schema', content)

    def testSchemaToElementRequiredSettings(self):
        # Minimum requirements for a Schema XML element
        schema = model.Schema(
            name='Foo',
            title=u'Foo',
            storage='eav',
            state='published',
            publish_date=datetime.date(2012, 03, 01)
            )

        xschema = schemaToElement(schema)
        self.assertEqual('schema', xschema.tag)
        self.assertEqual(schema.name, str(xschema.attrib['name']))
        self.assertEqual(schema.title, unicode(xschema.find('title').text))
        self.assertEqual(str(schema.publish_date), str(xschema.attrib['published']))

    def testSchemaToElementOptionalDescription(self):
        schema = model.Schema(
            name='Foo',
            title=u'Foo',
            storage='eav',
            state='published',
            publish_date=datetime.date(2012, 03, 01)
            )

        xschema = schemaToElement(schema)
        self.assertIsNone(xschema.find('description'))
        schema.description = u'Obvious description \n is obvious'
        xschema = schemaToElement(schema)
        self.assertEqual(schema.description, unicode(xschema.find('description').text))

    def testSchemaToElementOptionalAttribute(self):
        schema = model.Schema(
            name='Foo',
            title=u'Foo',
            storage='eav',
            state='published',
            publish_date=datetime.date(2012, 03, 01)
            )

        xschema = schemaToElement(schema)
        self.assertIsNone(xschema.find('attributes'))
        schema['foo'] = model.Attribute(title=u'foo', type='string', order=0)
        xschema = schemaToElement(schema)
        self.assertIsNotNone(xschema.find('attributes').find('attribute'))

    def testAttributeToElementRequiredSettings(self):
        # Minimum settings
        attribute = model.Attribute(name='foo', title=u'Foo', type='string')
        xattribute = attributeToElement(attribute)
        self.assertEqual('attribute', xattribute.tag)
        self.assertEqual(attribute.name, str(xattribute.attrib['name']))
        self.assertEqual(attribute.title, unicode(xattribute.find('title').text))
        self.assertEqual(attribute.type, str(xattribute.attrib['type']))

    def testAttributeToElementOptionalChecksum(self):
        attribute = model.Attribute(name='foo', title=u'Foo', type='string')
        xattribute = attributeToElement(attribute)
        # Optional checksum (if schema was previously exported)
        self.assertIsNone(xattribute.find('checksum'))
        attribute._checksum = 'ief0cn37'
        xattribute = attributeToElement(attribute)
        self.assertEqual(attribute.checksum, str(xattribute.find('checksum').text))

    def testAttributeToElementOptionalDescription(self):
        attribute = model.Attribute(name='foo', title=u'Foo', type='string')
        xattribute = attributeToElement(attribute)
        # Optional description
        self.assertIsNone(xattribute.find('description'))
        attribute.description = u'Describe \n all the things!'
        xattribute = attributeToElement(attribute)
        self.assertEqual(
            attribute.description, unicode(xattribute.find('description').text))

    def testAttributeToElementOptionalCollection(self):
        attribute = model.Attribute(name='foo', title=u'Foo', type='string')
        xattribute = attributeToElement(attribute)
        # Optional collection constraints
        self.assertIsNone(xattribute.find('collection'))
        attribute.is_collection = True
        xattribute = attributeToElement(attribute)
        self.assertIsNotNone(xattribute.find('collection'))

        with self.assertRaises(KeyError):
            xattribute.find('collection').attrib['min']
        attribute.collection_min = 4
        xattribute = attributeToElement(attribute)
        self.assertEqual(
            str(attribute.collection_min), str(xattribute.find('collection').attrib['min']))

        with self.assertRaises(KeyError):
            xattribute.find('collection').attrib['max']
        attribute.collection_max = 20
        xattribute = attributeToElement(attribute)
        self.assertEqual(
            str(attribute.collection_max), str(xattribute.find('collection').attrib['max']))

    def testAttributeToElementOptionalLimit(self):
        attribute = model.Attribute(name='foo', title=u'Foo', type='string')
        xattribute = attributeToElement(attribute)
        # Optional value limit
        self.assertIsNone(xattribute.find('limit'))
        attribute.value_min = 16
        xattribute = attributeToElement(attribute)
        self.assertIsNotNone(xattribute.find('limit'))
        self.assertEqual(
            str(attribute.value_min), str(xattribute.find('limit').attrib['min']))

        with self.assertRaises(KeyError):
            xattribute.find('limit').attrib['max']
        attribute.value_max = 32
        xattribute = attributeToElement(attribute)
        self.assertIsNotNone(xattribute.find('limit'))
        self.assertEqual(
            str(attribute.value_min), str(xattribute.find('limit').attrib['max']))

    def testAttributeToElementOptionalValidator(self):
        attribute = model.Attribute(name='foo', title=u'Foo', type='string')
        xattribute = attributeToElement(attribute)
        # Optional validator
        self.assertIsNone(xattribute.find('validator'))
        attribute.validator = '/.+/'
        xattribute = attributeToElement(attribute)
        self.assertEqual(attribute.validator, str(xattribute.find('validator').text))

    def testAttributeToElementOptionalChoice(self):
        attribute = model.Attribute(name='foo', title=u'Foo', type='string')
        xattribute = attributeToElement(attribute)
        # Optional choices
        self.assertIsNone(xattribute.find('choices'))
        attribute.choices.append(model.Choice(
            name='bar', title=u'Bar', value='abc', order=0))
        xattribute = attributeToElement(attribute)
        self.assertIsNotNone(xattribute.find('choices').find('choice'))

    def testAttributeToElementOptionalSubSchema(self):
        # Optional sub schemata
        attribute = model.Attribute(
            name='foo', title=u'Foo', type='object',
            object_schema=model.Schema(
                name='sub',
                title=u'Sub',
                state='published',
                storage='eav',
                publish_date=datetime.date(2012, 03, 01),
                )
            )
        xattribute = attributeToElement(attribute)
        self.assertIsNotNone(xattribute.find('schema'))

    def testChoiceToElement(self):
        choice = model.Choice(name='foo', title=u'Foo', value=u'abc123', order=0)
        xchoice = choiceToElement(choice)
        self.assertEqual('choice', xchoice.tag)
        self.assertEqual(choice.value, unicode(xchoice.attrib['value']))
        self.assertEqual(choice.title, unicode(xchoice.text))

    def testXmlToSchemaViaStream(self):
        session = self.layer['session']
        source = (
            u'<schema name="Foo" published="2012-03-01" storage="eav">'
            u'<title>Foo Schema</title>'
            u'</schema>'
            )

        file_ = StringIO(source)
        schema = importXml(session, file_)
        self.assertIsNotNone(schema.id)

    def testXmlToSchemaViaFileName(self):
        session = self.layer['session']
        source = (
            u'<schema name="Foo" published="2012-03-01" storage="eav">'
            u'<title>Foo Schema</title>'
            u'</schema>'
            )
        target = tempfile.NamedTemporaryFile(delete=False)
        target.close()
        with codecs.open(target.name, mode='w+b', encoding='utf-8') as stream:
            stream.write(source)

        schema = importXml(session, target.name)
        self.assertIsNotNone(schema.id)

    def testXmlToSchemaAlreadyExists(self):
        session = self.layer['session']
        source = (
            u'<schema name="Foo" published="2012-03-01" storage="eav">'
            u'<title>Foo Schema</title>'
            u'</schema>'
            )
        file_ = StringIO(source)
        schema = importXml(session, file_)

        # Can't import the same schema if one already exists for the (name, date)
        with self.assertRaises(AlreadyExistsError):
            schema = importXml(session, file_)

    def testElementToSchemaRequiredSettings(self):
        # Minimum settings
        xschema = E.schema(
            E.title(u'Foo'),
            name=u'Foo',
            storage='eav',
            published='2012-03-01'
            )

        schema = elementToSchema(xschema)
        self.assertEqual(schema.name, str(xschema.attrib['name']))
        self.assertEqual(schema.storage, str(xschema.attrib['storage']))
        self.assertEqual(str(schema.publish_date), str(xschema.attrib['published']))
        self.assertEqual(schema.title, unicode(xschema.title.text))

    def testElementToSchemaOptionalDescription(self):
        xschema = E.schema(
            E.title(u'Foo'),
            name=u'Foo',
            storage='eav',
            published='2012-03-01'
            )

        schema = elementToSchema(xschema)
        self.assertIsNone(schema.description)
        xschema.append(E.description(u'Clean \n all the things!'))
        schema = elementToSchema(xschema)
        self.assertEqual(schema.description, unicode(xschema.description.text))

    def testElementToSchemaOptionalAttribute(self):
        xschema = E.schema(
            E.title(u'Foo'),
            name=u'Foo',
            storage='eav',
            published='2012-03-01'
            )

        schema = elementToSchema(xschema)
        self.assertEqual(0, len(schema.attributes))
        xschema.append(E.attributes(
            E.attribute(E.title(u'Foo'), name='Foo', type='string')
            ))
        schema = elementToSchema(xschema)
        self.assertEqual(1, len(schema.attributes))

    def testElementToAttributeRequiredSettings(self):
        xattribute = E.attribute(E.title(u'Foo'), name='Foo', type='string')
        attribute = elementToAttribute(xattribute)
        self.assertEqual(attribute.name, str(xattribute.attrib['name']))
        self.assertEqual(attribute.type, str(xattribute.attrib['type']))
        self.assertEqual(attribute.title, unicode(xattribute.title.text))
        self.assertFalse(attribute.is_required)

    def testElementToAttributeOptionalRequired(self):
        xattribute = E.attribute(E.title(u'Foo'), name='Foo', type='string')
        attribute = elementToAttribute(xattribute)

        xattribute.set('required', 'True')
        attribute = elementToAttribute(xattribute)
        self.assertTrue(attribute.is_required)
        xattribute.set('required', 'False')
        attribute = elementToAttribute(xattribute)
        self.assertFalse(attribute.is_required)

    def testElementToAttributeOptionalDescription(self):
        xattribute = E.attribute(E.title(u'Foo'), name='Foo', type='string')
        attribute = elementToAttribute(xattribute)
        self.assertIsNone(attribute.description)
        xattribute.append(E.description(u'Why not \n zoidberg?'))
        attribute = elementToAttribute(xattribute)
        self.assertEqual(attribute.description, unicode(xattribute.description.text))

    def testElementToAttributeOptionalChecksum(self):
        xattribute = E.attribute(E.title(u'Foo'), name='Foo', type='string')
        attribute = elementToAttribute(xattribute)
        self.assertIsNone(attribute.checksum)
        xattribute.append(E.checksum(u'3fjdfdfa'))
        attribute = elementToAttribute(xattribute)
        self.assertEqual(attribute.checksum, str(xattribute.checksum.text))

    def testElementToAttributeOptionalCollection(self):
        xattribute = E.attribute(E.title(u'Foo'), name='Foo', type='string')
        attribute = elementToAttribute(xattribute)

        self.assertFalse(attribute.is_collection)
        xattribute.append(E.collection())
        attribute = elementToAttribute(xattribute)
        self.assertTrue(attribute.is_collection)

        # Optional collection minimum length
        self.assertIsNone(attribute.collection_min)
        with self.assertRaises(ValueError):
            xattribute.collection.set('min', 'foo')
            attribute = elementToAttribute(xattribute)
        xattribute.collection.set('min', '134')
        attribute = elementToAttribute(xattribute)
        self.assertEqual(attribute.collection_min, int(xattribute.collection.attrib['min']))

        # Optional collection maximum length
        self.assertIsNone(attribute.collection_max)
        with self.assertRaises(ValueError):
            xattribute.collection.set('max', 'foo')
            attribute = elementToAttribute(xattribute)
        xattribute.collection.set('max', '134')
        attribute = elementToAttribute(xattribute)
        self.assertEqual(attribute.collection_max, int(xattribute.collection.attrib['max']))

    def testElementToAttributeOptionalLimit(self):
        xattribute = E.attribute(E.title(u'Foo'), name='Foo', type='string')
        attribute = elementToAttribute(xattribute)

        xattribute.append(E.limit())

        # Optinal value minimum
        self.assertIsNone(attribute.value_min)
        with self.assertRaises(ValueError):
            xattribute.limit.set('min', 'foo')
            attribute = elementToAttribute(xattribute)
        xattribute.limit.set('min', '134')
        attribute = elementToAttribute(xattribute)
        self.assertEqual(attribute.value_min, int(xattribute.limit.attrib['min']))

        # Optinal value maximum
        self.assertIsNone(attribute.value_max)
        with self.assertRaises(ValueError):
            xattribute.limit.set('max', 'foo')
            attribute = elementToAttribute(xattribute)
        xattribute.limit.set('max', '134')
        attribute = elementToAttribute(xattribute)
        self.assertEqual(attribute.value_max, int(xattribute.limit.attrib['max']))

    def testElementToAttributeOptionalValidator(self):
        xattribute = E.attribute(E.title(u'Foo'), name='Foo', type='string')
        attribute = elementToAttribute(xattribute)
        # Optinoal validator
        self.assertIsNone(attribute.validator)
        xattribute.append(E.validator('/.+/'))
        attribute = elementToAttribute(xattribute)
        self.assertEqual(attribute.validator, str(xattribute.validator.text))

    def testElementToAttributeOptionalChoices(self):
        xattribute = E.attribute(E.title(u'Foo'), name='Foo', type='string')
        attribute = elementToAttribute(xattribute)
        # Optional choices
        self.assertEqual(0, len(attribute.choices))
        xattribute.append(E.choices())
        attribute = elementToAttribute(xattribute)
        self.assertEqual(0, len(attribute.choices))
        xattribute.choices.append(E.choice('Foo', value='foo'))
        attribute = elementToAttribute(xattribute)
        self.assertEqual(1, len(attribute.choices))
        self.assertEqual(0, attribute.choices[0].order)

    def testElementToAttributeOptionalSubSchema(self):
        xattribute = E.attribute(E.title(u'Foo'), name='Foo', type='string')
        attribute = elementToAttribute(xattribute)
        # Optional sub schema
        self.assertIsNone(attribute.object_schema)
        xattribute = E.attribute(
            E.title(u'Foo'),
            E.schema(E.title('Sub'), name='Sub', storage='eav', published='2012-04-10'),
            name='Foo',
            type='object',
            )
        attribute = elementToAttribute(xattribute)
        self.assertIsNotNone(attribute.object_schema)
        self.assertEqual(attribute.object_schema.name, str(xattribute.schema.attrib.get('name')))

    def testElementToChoice(self):
        xchoice = E.choice(u'Foo', value=u'abc123')
        choice = elementToChoice(xchoice)
        self.assertEqual(choice.title, unicode(xchoice.text))
        self.assertEqual(choice.value, unicode(xchoice.attrib['value']))

