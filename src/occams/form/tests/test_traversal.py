import unittest2 as unittest

from zope.browser.interfaces import IBrowserView
from zope.publisher.browser import TestRequest
from zExceptions import NotFound
from z3c.saconfig import named_scoped_session

from occams.datastore import model
from occams.form.traversal import SchemaContext
from occams.form.traversal import AttributeContext
from occams.form.traversal import RepositoryTraverser
from occams.form.traversal import SchemaTraverser
from occams.form.traversal import AttributeTraverser
from occams.form.interfaces import ISchemaContext
from occams.form.interfaces import IAttributeContext
from occams.form.interfaces import DATA_KEY
from occams.form.testing import OCCAMS_FORM_INTEGRATION_TESTING
from occams.form.testing import SESSION_NAME


class TestTraversal(unittest.TestCase):

    layer = OCCAMS_FORM_INTEGRATION_TESTING

    def testBasic(self):
        """
        Make sure default behavior still works (i.e. views)
        """
        portal = self.layer['portal']
        request = TestRequest()
        repository = portal['test-repository']
        traverser = RepositoryTraverser(repository, request)
        with self.assertRaises(NotFound, msg='Traversed to empty context!'):
            traverser.publishTraverse(request, 'evil')
        view = traverser.publishTraverse(request, 'view')
        self.assertTrue(IBrowserView.providedBy(view), 'Invalid view!')

    def testFromRepository(self):
        """
        Tests schema lookups from a repository context
        """
        portal = self.layer['portal']
        request = TestRequest()
        repository = portal['test-repository']
        traverser = RepositoryTraverser(repository, request)

        # Make sure we can't traverse to anything that doesn't exist
        context = traverser.traverse('Evil')
        self.assertIsNone(context, 'Traversed to empty context!')

        # Now add some data, we should be able to traverse to it
        # Note that it is up to the views on how to display expired data
        session = named_scoped_session(SESSION_NAME)
        schema = model.Schema(name='Foo', title=u'Foo Form', storage='eav')
        session.add(schema)
        session.flush()

        context = traverser.traverse('Foo')
        self.assertIsNotNone(context, 'Traversal failed!')
        self.assertTrue(ISchemaContext.providedBy(context), 'Invalid context!')

    def testFromSchema(self):
        """
        Tests field lookups from a form context
        Note that beyond a repository context is pure form annotation data
        since it's assumed that we'll be editing the form.
        """
        request = TestRequest()

        fieldData = dict(name='bar', title=u'Bar Field')
        formData = dict(name='Test', title=u'Test Form', fields=dict(bar=fieldData))

        browserSession = ISession(request)
        browserSession[DATA_KEY] = {formData['name']: formData}
        browserSession.save()

        traverser = SchemaTraverser(SchemaContext(data=formData), request)

        context = traverser.traverse('evil')
        self.assertIsNone(context, 'Traversed to empty context!')

        context = traverser.traverse('bar')
        self.assertIsNotNone(context, 'Traversal failed!')
        self.assertTrue(IAttributeContext.providedBy(context), 'Invalid context!')

    def testFromAttrubute(self):
        """
        Tests sub-field lookups from a field context
        """
        request = TestRequest()

        subFieldData = dict(name='baz', title=u'Baz Field')
        subFormData = dict(name='Sub', title=u'Sub Form', fields=dict(baz=subFieldData))
        fieldData = dict(name='bar', title=u'Bar Field', schema=subFormData)
        formData = dict(name='Test', title=u'Test Form', fields=dict(bar=fieldData))

        browserSession = ISession(request)
        browserSession[DATA_KEY] = {formData['name']: formData}
        browserSession.save()

        traverser = AttributeTraverser(AttributeContext(data=fieldData), request)

        context = traverser.traverse('evil')
        self.assertIsNone(context, 'Traversed to empty context!')

        context = traverser.traverse('baz')
        self.assertIsNotNone(context, 'Traversal failed!')
        self.assertTrue(IAttributeContext.providedBy(context), 'Invalid context!')
