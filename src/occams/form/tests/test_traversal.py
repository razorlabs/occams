import unittest2 as unittest

from occams.form.testing import OCCAMS_FORM_INTEGRATION_TESTING
from occams.form.testing import SESSION_NAME

from zope.browser.interfaces import IBrowserView
from z3c.saconfig import named_scoped_session

from avrc.data.store import model
from occams.form.traversal import RepositoryTraverse
from occams.form.interfaces import ISchemaContext
from occams.form.interfaces import IAttributeContext


class TestTraversal(unittest.TestCase):

    layer = OCCAMS_FORM_INTEGRATION_TESTING

    def testBasic(self):
        """
        Make sure default behavior still works (i.e. views)
        """
        portal = self.layer['portal']
        request = self.layer['request']
        repository = portal['test-repository']
        traverser = RepositoryTraverse(repository, request)
        view = traverser.publishTraverse(request, 'view')
        self.assertTrue(IBrowserView.providedBy(view), 'Cannot traverse to view!')

    def testRepository(self):
        """
        Tests schema lookups from a repository context
        """
        portal = self.layer['portal']
        request = self.layer['request']
        repository = portal['test-repository']
        traverser = RepositoryTraverse(repository, request)

        # Make sure we can't traverse to anything that doesn't exist
        context = traverser.traverse('Evil')
        self.assertTrue(context is None, 'Apparently an empty context exists')

        # Now add some data, we should be able to traverse to it
        # Note that it is up to the views on how to display expired data
        session = named_scoped_session(SESSION_NAME)
        schema = model.Schema(name='Foo', title=u'Foo Form', storage='eav')
        session.add(schema)
        session.flush()
        context = traverser.traverse('Foo')
        self.assertTrue(ISchemaContext.providedBy(context), 'Schema not found')

    def testForm(self):
        """
        Tests field lookups from a form context
        Note that beyond a repository context is pure form annotation data
        since we'll be editing the form.
        """
        portal = self.layer['portal']
        request = self.layer['request']
        repository = portal['test-repository']
        traverser = RepositoryTraverse(repository, request)

#        # Make sure we can't traverse to anything that doesn't exist
#        context = traverser.traverse('Evil')
#        self.assertTrue(context is None, 'Apparently an empty context exists')
#
#        # Now add some data, we should be able to traverse to it
#        # Note that it is up to the views on how to display expired data
#        session = named_scoped_session(SESSION_NAME)
#        schema = model.Schema(name='Foo', title=u'Foo Form', storage='eav')
#        session.add(schema)
#        session.flush()
#        context = traverser.traverse('Foo')
#        self.assertTrue(ISchemaContext.providedBy(context), 'Schema not found')

    def testField(self):
        """
        Tests sub-field lookups from a field context
        """


