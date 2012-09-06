import unittest2 as unittest

from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
import zope.interface

from occams.form import testing
from occams.form.browser import listing


class SummaryListingFormTestCase(unittest.TestCase):

    layer = testing.OCCAMS_FORM_INTEGRATION_TESTING

    def test_add_without_description(self):
        portal = self.layer[u'portal']
        http_request = self.layer[u'request']

        setRoles(portal, TEST_USER_ID, ['Manager'])
        portal.invokeFactory(u'occams.form.repository', 'r1',
            title=u'Forms',
            session=testing.SESSION_NAME
            )
        setRoles(portal, TEST_USER_ID, ['Member'])

        repository = portal[u'r1']

        listing_view = listing.SummaryListingForm(repository, http_request)

        schema = listing_view.add(dict(
            title=u'Sample Form',
            description=None,
            ))

        # Make sure the description isn't wrapped to string
        self.assertIsNone(schema.description, msg=u'Description was set')

    def test_add_with_description(self):
        portal = self.layer[u'portal']
        http_request = self.layer[u'request']

        setRoles(portal, TEST_USER_ID, ['Manager'])
        portal.invokeFactory(u'occams.form.repository', 'r1',
            title=u'Forms',
            session=testing.SESSION_NAME
            )
        setRoles(portal, TEST_USER_ID, ['Member'])

        repository = portal[u'r1']

        listing_view = listing.SummaryListingForm(repository, http_request)

        expected_description = u'Some random description'
        schema = listing_view.add(dict(
            title=u'Sample Form',
            description=expected_description,
            ))

        self.assertEqual(expected_description, schema.description)

