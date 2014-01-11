from datetime import date

from ddt import ddt, data
import mock
from pyramid import testing
from webob.multidict import MultiDict
import transaction

from occams.clinical import Session, models
from tests import FunctionalFixture, IntegrationFixture


@ddt
class TestListView(FunctionalFixture):

    @data('administrator', 'investigator', 'statistician', 'researcher',
          'nurse')
    def test_allowed(self, principal):
        """
        It should allow administrative personnel to access the view
        """
        ENVIRON = self.make_environ(groups=[principal])
        response = self.app.get('/data', extra_environ=ENVIRON)
        self.assertEqual(response.status_code, 200)

    @data('assistant', 'student', None)
    def test_not_allowed(self, principal):
        """
        It should not allow data entry prinicipals to access the view
        """
        ENVIRON = self.make_environ(groups=[principal])
        response = self.app.get('/data', extra_environ=ENVIRON, status='*')
        self.assertIn(response.status_code, (401, 403))

    def test_unauthenticated_not_allowed(self):
        """
        It should not allow unauthenticated users access the view
        """
        response = self.app.get('/data', status='*')
        self.assertIn(response.status_code, (401, 403))


class TestList(IntegrationFixture):

    def setUp(self):
        super(TestList, self).setUp()
        self.config.include('pyramid_beaker')
        # Use permissive since we're using functional tests for permissions
        self.config.testing_securitypolicy(userid='joe',
                                           permissive=True)
        self.add_user('joe')
        from occams.clinical.views.data import list_
        self.view_func = list_

    def test_get_schemata(self):
        """
        It should render only published schemata
        """
        # No schemata
        request = testing.DummyRequest(
            layout_manager=mock.Mock())
        response = self.view_func(request)
        self.assertFalse(response['has_schemata'])

        # Not-yet-published schemata
        schema = models.Schema(
            name=u'vitals', title=u'Vitals')
        Session.add(schema)
        Session.flush()
        response = self.view_func(request)
        self.assertFalse(response['has_schemata'])

        # Published schemata
        schema.publish_date = date.today()
        Session.flush()
        response = self.view_func(request)
        self.assertTrue(response['has_schemata'])

    def test_post_empty(self):
        """
        It should raise validation errors on empty imput
        """
        request = testing.DummyRequest(
            layout_manager=mock.Mock(),
            post=MultiDict())
        response = self.view_func(request)
        self.assertIsNotNone(response['form'].field['schemata'].error.msg)

    def test_post_non_existent_schema(self):
        """
        It should raise validation errors for non-existent schemata
        """
        request = testing.DummyRequest(
            layout_manager=mock.Mock(),
            post=MultiDict([('schemata', '1')]))
        response = self.view_func(request)
        self.assertIsNotNone(response['form'].field['schemata'].error.msg)

    def test_post_invalid_csrf(self):
        """
        It should check for cross-site forgery
        """
        request = testing.DummyRequest(
            layout_manager=mock.Mock(),
            post=MultiDict([('csrf_token', 'd3v10us')]))
        response = self.view_func(request)
        self.assertIsNotNone(response['form'].field['csrf_token'].error.msg)

    def test_valid(self):
        """
        It should add an export record and initiate an async task
        """
        self.config.add_route('data_download', '/data/downloads')
        with transaction.manager:
            schema = models.Schema(
                name=u'vitals', title=u'Vitals', publish_date=date.today())
            Session.add(schema)
            Session.flush()
            schema_id = schema.id

        request = testing.DummyRequest(
            layout_manager=mock.Mock(),
            post=MultiDict([
                ('schemata', str(schema_id))
                ]))
        request.POST['csrf_token'] = request.session.get_csrf_token()
        # Don't actually trigger the asynchrnous task,
        # that will be tested elsewhere
        with mock.patch('occams.clinical.tasks.make_export.s'):
            response = self.view_func(request)

        self.assertEqual(response.location,
                         request.route_path('data_download'))
        export = Session.query(models.Export).one()
        self.assertEqual(export.owner_user.key, 'joe')
        self.assertEqual(export.schemata[0].id, schema_id)


class TestAttachementView(FunctionalFixture):
    pass

