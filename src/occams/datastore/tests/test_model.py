
import unittest2 as unittest
from datetime import datetime

from zope.interface.interface import InterfaceClass
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject

import sqlalchemy.exc

from occams.datastore import model


from occams.datastore.testing import DATABASE_LAYER


class SchemaTestCase(unittest.TestCase):
    """
    Verifies DataStore compatibility with Zope-style schema
    """


    layer = DATABASE_LAYER

    def testBasic(self):
        schema = model.Schema(name='Foo')
        self.fail()
