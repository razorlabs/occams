import datetime
import unittest2 as unittest

import sqlalchemy.exc
from occams.datastore import model
from occams.datastore.testing import DATASTORE_LAYER
from occams.datastore.users import UserManager


class UserModelTestCase(unittest.TestCase):
    """
    Verifies user storage
    """

    layer = DATASTORE_LAYER

    def testAdd(self):
        session = self.layer['session']

        # Try adding a faulty user
        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            user = model.User()
            session.add(user)
            session.flush()

        # That should have not worked, in which case we'll clear the transaction
        session.rollback()

        # Try adding a valid user now
        user = model.User(key='mr.foo@foomail.com')
        session.add(user)
        session.flush()
        self.assertIsNotNone(user.id, 'User was not flushed')

        # Make sure the dates are valid
        self.assertEqual(user.create_date, user.modify_date, 'Different create dates')

        # Make sure we can't use an incorrect timeline
        user.create_date += datetime.timedelta(1)

        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            session.flush()

        # Clear the transaction in case we want to do anything else
        session.rollback()

    def testRemoteFailOnActiveUser(self):
        # Should not be able to remove a user that has modified the data
        pass


class UserManagerTestCase(unittest.TestCase):

    layer = DATASTORE_LAYER

    def testKeys(self):
        session = self.layer['session']
        manager = UserManager(session)

        self.assertNotIn('foo@foo.com', manager.keys())

        session.add(model.User(key='foo@foo.com'))
        session.flush()
        self.assertIn('foo@foo.com', manager.keys())

    def testHas(self):
        pass

    def testPurge(self):
        pass

    def testPut(self):
        pass

    def testGet(self):
        pass
