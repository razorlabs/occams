import unittest2 as unittest

from z3c.saconfig import named_scoped_session

from hive.roster.testing import OCCAMS_ROSTER_INTEGRATION_TESTING
from hive.roster import model
from hive.roster.interfaces import START_ID

class TestDataBaseSetup(unittest.TestCase):
    """
    Test database installation
    """

    layer = OCCAMS_ROSTER_INTEGRATION_TESTING

    def testStartingPoint(self):
        """
        Ensure that the OUR numbers can be generated at the correct starting id
        """
        session = named_scoped_session(u'hive.roster.Session')
        identifier = model.Identifier(origin=model.Site(title=u'Foo'))
        session.add(identifier)
        session.flush()

        self.assertGreaterEqual(identifier.id, START_ID,
            msg=u'OUR number id starting point not installed correctly'
            )

