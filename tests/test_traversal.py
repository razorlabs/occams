import unittest2 as unittest

from plone.dexterity import utils
import zExceptions
from z3c import saconfig
from zope.browser.interfaces import IBrowserView

from occams.datastore import model

from occams.form import traversal
from occams.form import interfaces
from occams.form import testing


class TraversalTestCase(unittest.TestCase):

    layer = testing.OCCAMS_FORM_INTEGRATION_TESTING

    def test_views(self):
        u"""
        Make sure default behavior still works (i.e. views)
        """
        portal = self.layer['portal']
        request = self.layer['request']
        repository = utils.createContentInContainer(
            checkConstraints=False,
            container=portal,
            portal_type=u'occams.form.repository',
            title=u'Forms',
            session=testing.SESSION_NAME,
            )
        traverser = traversal.RepositoryTraverser(repository, request)
        with self.assertRaises(zExceptions.NotFound, msg='Traversed to empty context!'):
            traverser.publishTraverse(request, 'evil')
        view = traverser.publishTraverse(request, 'view')
        self.assertTrue(IBrowserView.providedBy(view), 'Invalid view!')

    def test_from_repository(self):
        u"""
        Tests schema lookups from a repository context
        """
        portal = self.layer['portal']
        request = self.layer['request']
        repository = utils.createContentInContainer(
            checkConstraints=False,
            container=portal,
            portal_type=u'occams.form.repository',
            title=u'Forms',
            session=testing.SESSION_NAME,
            )
        traverser = traversal.RepositoryTraverser(repository, request)

        # Make sure we can't traverse to anything that doesn't exist
        context = traverser.traverse('Evil')
        self.assertIsNone(context, 'Traversed to empty context!')

        # Now add some data, we should be able to traverse to it
        # Note that it is up to the views on how to display expired data
        session = saconfig.named_scoped_session(testing.SESSION_NAME)
        schema = model.Schema(name='Foo', title=u'Foo Form', storage='eav')
        session.add(schema)
        session.flush()

        context = traverser.traverse('Foo')
        self.assertIsNotNone(context, 'Traversal failed!')
        self.assertTrue(interfaces.ISchemaContext.providedBy(context), 'Invalid context!')

    def test_from_schema(self):
        u"""
        Tests field lookups from a form context
        Note that beyond a repository context is pure form annotation data
        since it's assumed that we'll be editing the form.
        """
        request = self.layer['request']

        fieldData = dict(name='bar', title=u'Bar Field')
        formData = dict(name='Test', title=u'Test Form', fields=dict(bar=fieldData))

        traverser = traversal.SchemaTraverser(traversal.SchemaContext(data=formData), request)

        context = traverser.traverse('evil')
        self.assertIsNone(context, 'Traversed to empty context!')

        context = traverser.traverse('bar')
        self.assertIsNotNone(context, 'Traversal failed!')
        self.assertTrue(interfaces.IAttributeContext.providedBy(context), 'Invalid context!')

    def test_from_attribute(self):
        u"""
        Tests sub-field lookups from a field context
        """
        request = self.layer['request']

        subFieldData = dict(name='baz', title=u'Baz Field')
        subFormData = dict(name='Sub', title=u'Sub Form', fields=dict(baz=subFieldData))
        fieldData = dict(name='bar', title=u'Bar Field', schema=subFormData)
        formData = dict(name='Test', title=u'Test Form', fields=dict(bar=fieldData))

        traverser = traversal.AttributeTraverser(traversal.AttributeContext(data=fieldData), request)

        context = traverser.traverse('evil')
        self.assertIsNone(context, 'Traversed to empty context!')

        context = traverser.traverse('baz')
        self.assertIsNotNone(context, 'Traversal failed!')
        self.assertTrue(interfaces.IAttributeContext.providedBy(context), 'Invalid context!')

