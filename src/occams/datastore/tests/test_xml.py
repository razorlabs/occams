import datetime
import tempfile
import lxml.etree
import unittest2 as unittest

import sqlalchemy.exc
from occams.datastore import model
from occams.datastore.testing import DATASTORE_LAYER
from occams.datastore.xml import schemaToXml
from occams.datastore.xml import xmlToSchema
from occams.datastore.xml import exportToXml
from occams.datastore.xml import importFromXml


class XmlTestCase(unittest.TestCase):

    layer = DATASTORE_LAYER

    def testBasic(self):
        session = self.layer['session']
        schema = model.Schema(
            name='Foo',
            title=u'Foo',
            state='published',
            publish_date=datetime.date(2012, 03, 01),
            attributes=dict(
                foo=model.Attribute(name='foo', title=u'Foo', type='string', order=0),
                bar=model.Attribute(name='bar', title=u'Bar', type='integer', order=1,
                    choices=[
                        model.Choice(name='foo', title=u'Foo', value=12312, order=0),
                        model.Choice(name='bar', title=u'Bar', value=2542342, order=1),
                        model.Choice(name='baz', title=u'Baz', value=598494, order=2),
                        ]
                    )
                )
            )
        session.add(schema)
        session.flush()
        xml = schemaToXml(schema)
        print
        print lxml.etree.tounicode(xml, pretty_print=True)
        print
