from datetime import date

from ddt import ddt, data
import mock
from pyramid import testing
from webob.multidict import MultiDict

from occams.clinical import Session, models
from tests import IntegrationFixture


class TestAdd(IntegrationFixture):

    def setUp(self):
        super(TestAdd, self).setUp()
        # Use permissive since we're using functional tests for permissions
        self.config.testing_securitypolicy(userid='joe', permissive=True)
        from occams.clinical.views.export import add
        self.view_func = add

    def test_get_schemata(self):
        """
        It should render only published schemata
        """
        from tests import add_user
        # No schemata
        request = testing.DummyRequest(
            layout_manager=mock.Mock())
        response = self.view_func(request)
        self.assertEquals(response['schemata_count'], 0)

        add_user('joe')

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
        from pyramid.httpexceptions import HTTPFound
        from tests import add_user
        self.config.include('occams.clinical.routes')
        self.config.registry.settings['app.export.dir'] = '/tmp'

        add_user('joe')
        schema = models.Schema(
            name=u'vitals', title=u'Vitals', publish_date=date.today())
        Session.add(schema)
        Session.flush()

        request = testing.DummyRequest(
            layout_manager=mock.Mock(),
            post=MultiDict([
                ('contents', str('vitals'))
            ]))
        request.POST['csrf_token'] = request.session.get_csrf_token()
        response = self.view_func(request)

        self.assertIsInstance(response, HTTPFound)
        self.assertEqual(response.location,
                         request.route_path('export_status'))
        export = Session.query(models.Export).one()
        self.assertEqual(export.owner_user.key, 'joe')

    def test_exceed_limit(self):
        """
        It should not let the user exceed their allocated export limit
        """
        import deform
        from tests import add_user
        self.config.registry.settings['app.export.limit'] = '1'

        add_user('joe')
        previous_export = models.Export(
            owner_user=Session.query(models.User).filter_by(key='joe').one(),
            contents=[{
                u'name': u'vitals',
                u'title': u'Vitals',
                u'versions': [str(date.today())]}])
        Session.add(previous_export)
        Session.flush()

        # The renderer should know about it
        request = testing.DummyRequest(
            layout_manager=mock.Mock())
        response = self.view_func(request)
        self.assertTrue(response['exceeded'])

        # If the user insists, they'll get a validation error as well
        request = testing.DummyRequest(
            layout_manager=mock.Mock(),
            post=MultiDict([
                ('contents', 'vitals')
                ]))
        request.POST['csrf_token'] = request.session.get_csrf_token()
        response = self.view_func(request)
        self.assertIsInstance(response['form'], deform.ValidationFailure)
        self.assertEqual(response['form'].error.msg, u'Export limit exceeded')


class TestExport(IntegrationFixture):

    def setUp(self):
        super(TestExport, self).setUp()
        # Use permissive since we're using functional tests for permissions
        self.config.testing_securitypolicy(userid='joe', permissive=True)
        from occams.clinical.views.export import export
        self.view_func = export

    def test_get_current_user(self):
        """
        It should return the authenticated user's exports
        """
        from tests import add_user
        add_user('jane')
        add_user('joe')
        Session.add_all([
            models.Export(
                owner_user=(
                    Session.query(models.User)
                    .filter_by(key='joe')
                    .one()),
                status='complete'),
            models.Export(
                owner_user=(
                    Session.query(models.User)
                    .filter_by(key='jane')
                    .one()),
                status='pending')])
        Session.flush()

        request = testing.DummyRequest(
            layout_manager=mock.Mock())
        response = self.view_func(request)
        export = response['exports'].one()
        self.assertEquals(export.owner_user.key, 'joe')

    def test_ignore_expired(self):
        """
        It should not render expired exports.
        """
        from datetime import datetime, timedelta
        from tests import add_user

        EXPIRE_DAYS = 10
        self.config.registry.settings['app.export.expire'] = '10'
        add_user('joe')
        now = datetime.now()
        Session.add_all([
            models.Export(
                owner_user=(
                    Session.query(models.User)
                    .filter_by(key='joe')
                    .one()),
                status='complete',
                create_date=now - timedelta(EXPIRE_DAYS + 1)),
            models.Export(
                owner_user=(
                    Session.query(models.User)
                    .filter_by(key='joe')
                    .one()),
                status='pending',
                create_date=now)])
        Session.flush()

        request = testing.DummyRequest(
            layout_manager=mock.Mock())
        response = self.view_func(request)
        self.assertEquals(response['exports_count'], 1)
        export = response['exports'].one()
        self.assertEquals(export.create_date, now)


@ddt
class TestDownload(IntegrationFixture):

    def setUp(self):
        super(TestDownload, self).setUp()
        # Use permissive since we're using functional tests for permissions
        self.config.testing_securitypolicy(userid='joe', permissive=True)
        from occams.clinical.views.export import download
        self.view_func = download

    def test_get_owner_exports(self):
        """
        It should only allow owners of the export to download it
        """
        from pyramid.httpexceptions import HTTPNotFound
        from pyramid.response import FileResponse
        from tests import add_user

        self.config.registry.settings['app.export.dir'] = '/tmp'
        add_user('joe')
        add_user('jane')
        Session.add(models.Export(
            id=123,
            owner_user=(
                Session.query(models.User)
                .filter_by(key='jane')
                .one()),
            status='complete'))
        Session.flush()

        self.config.testing_securitypolicy(userid='joe', permissive=True)
        request = testing.DummyRequest(
            layout_manager=mock.Mock(),
            matchdict={'export_id': 123})
        with self.assertRaises(HTTPNotFound):
            self.view_func(request)

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
        from pyramid.httpexceptions import HTTPNotFound
        from tests import add_user

        add_user('joe')
        Session.add(models.Export(
            id=123,
            owner_user=(
                Session.query(models.User)
                .filter_by(key='joe')
                .one()),
            status=status))

        request = testing.DummyRequest(
            layout_manager=mock.Mock(),
            matchdict={'export_id': 123})
        with self.assertRaises(HTTPNotFound):
            self.view_func(request)
