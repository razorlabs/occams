import datetime
import unittest2 as unittest

import sqlalchemy.exc
from occams.datastore import model
from occams.datastore.testing import DATASTORE_LAYER


class ModifiableMixinTestCase(unittest.TestCase):
    """
    Verifies modifiable extensions
    """

    layer = DATASTORE_LAYER

    def testExtension(self):
        """
        Test is new mappings obey the modifiable extension properly
        """
        session = self.layer['session']
        schema = model.Schema(name='Foo', title=u'')
        session.add(schema)
        session.flush()

        message = 'No metadata added to '
        for check in ('create_date', 'create_user_id', 'modify_date', 'modify_user_id'):
            self.assertIsNotNone(getattr(schema, check), message)

        # Make sure we can't use an incorrect timeline
        schema.create_date += datetime.timedelta(1)

        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            session.flush()

        # Clear the transaction in case we want to do anything else
        session.rollback()
