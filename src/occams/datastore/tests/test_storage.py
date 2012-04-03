"""
Tests for storage implementations and services
"""

import unittest2 as unittest
from datetime import date

import sqlalchemy.exc
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject

from occams.datastore import model
from occams.datastore.interfaces import IManager
from occams.datastore.item import ItemFactory
from occams.datastore.testing import DATASTORE_LAYER


p1 = date(2012, 3, 1)
p2 = date(2012, 4, 1)
p3 = date(2012, 5, 1)
p4 = date(2012, 6, 1)


class EntityToItemTestCase(unittest.TestCase):

    layer = DATASTORE_LAYER

    def testBasic(self):
        session = self.layer['session']

    def testSubObject(self):
        session = self.layer['session']


class ItemToEntityTestCase(unittest.TestCase):

    layer = DATASTORE_LAYER

    def testBasic(self):
        session = self.layer['session']

    def testSubObject(self):
        session = self.layer['session']
