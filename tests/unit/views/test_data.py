from datetime import date

from ddt import ddt, data
import mock
from pyramid import testing
from webob.multidict import MultiDict

from occams.clinical import Session, models
from tests import IntegrationFixture


class TestList(IntegrationFixture):

    def setUp(self):
        super(TestList, self).setUp()
        # Use permissive since we're using functional tests for permissions
        self.config.testing_securitypolicy(userid='joe', permissive=True)
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
        self.assertEquals(response['schemata_count'], 0)

        self.add_user('joe')

        # Not-yet-published schemata
        schema = models.Schema(
            name=u'vitals', title=u'Vitals')
        Session.add(schema)
        Session.flush()
        request = testing.DummyRequest(
            layout_manager=mock.Mock())
        response = self.view_func(request)
        self.assertEquals(response['schemata_count'], 0)

        # Published schemata
        schema.publish_date = date.today()
        Session.flush()
        request = testing.DummyRequest(
            layout_manager=mock.Mock())
        response = self.view_func(request)
        self.assertEquals(response['schemata_count'], 1)

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

    # Don't actually invoke the subtasks
    @mock.patch('occams.clinical.tasks.make_export')
    def test_valid(self, make_export):
        """
        It should add an export record and initiate an async task
        """
        self.config.add_route('data_export', '/data/exports')
        self.config.registry.settings['app.export_dir'] = '/tmp'

        self.add_user('joe')
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
        response = self.view_func(request)

        self.assertEqual(response.location, request.route_path('data_export'))
        export = Session.query(models.Export).one()
        self.assertEqual(export.owner_user.key, 'joe')
        self.assertEqual(export.schemata[0].id, schema_id)


class TestExport(IntegrationFixture):

    def setUp(self):
        super(TestExport, self).setUp()
        # Use permissive since we're using functional tests for permissions
        self.config.testing_securitypolicy(userid='joe', permissive=True)
        from occams.clinical.views.data import export
        self.view_func = export

    def test_get(self):
        """
        It should return the authenticated user's exports
        """
        # No schemata
        request = testing.DummyRequest(
            layout_manager=mock.Mock())
        response = self.view_func(request)
        self.assertEquals(response['exports_count'], 0)

        # Not-yet-published schemata
        self.add_user('joe')
        Session.add(models.Export(
            id=123,
            owner_user=(
                Session.query(models.User)
                .filter_by(key='joe')
                .one()),
            status='complete'))
        Session.flush()
        request = testing.DummyRequest(
            layout_manager=mock.Mock())
        response = self.view_func(request)
        self.assertEquals(response['exports_count'], 1)


@ddt
class TestDownload(IntegrationFixture):

    def setUp(self):
        super(TestDownload, self).setUp()
        # Use permissive since we're using functional tests for permissions
        self.config.testing_securitypolicy(userid='joe', permissive=True)
        from occams.clinical.views.data import download
        self.view_func = download

    def test_get_owner_exports(self):
        """
        It should only allow owners of the export to download it
        """
        self.config.registry.settings['app.export_dir'] = '/tmp'
        self.add_user('joe')
        self.add_user('jane')
        Session.add(models.Export(
            id=123,
            owner_user=(
                Session.query(models.User)
                .filter_by(key='jane')
                .one()),
            status='complete'))
        Session.flush()

        self.config.testing_securitypolicy(userid='joe', permissive=True)
        from pyramid.httpexceptions import HTTPNotFound
        request = testing.DummyRequest(
            layout_manager=mock.Mock(),
            matchdict={'export_id': 123})
        with self.assertRaises(HTTPNotFound):
            self.view_func(request)

        from pyramid.response import FileResponse
        self.config.testing_securitypolicy(userid='jane', permissive=True)
        request = testing.DummyRequest(
            layout_manager=mock.Mock(),
            matchdict={'export_id': 123})
        response = self.view_func(request)
        self.assertIsInstance(response, FileResponse)

    @data('failed', 'pending')
    def test_get_not_found_status(self, status):
        """
        It should return 404 if the record is not ready
        """
        self.add_user('joe')
        Session.add(models.Export(
            id=123,
            owner_user=(
                Session.query(models.User)
                .filter_by(key='joe')
                .one()),
            status=status))

        from pyramid.httpexceptions import HTTPNotFound
        request = testing.DummyRequest(
            layout_manager=mock.Mock(),
            matchdict={'export_id': 123})
        with self.assertRaises(HTTPNotFound):
            self.view_func(request)
