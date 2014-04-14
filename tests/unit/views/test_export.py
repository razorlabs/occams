from datetime import date

from ddt import ddt, data
import mock
from pyramid import testing
from webob.multidict import MultiDict

from occams.studies import Session, models
from tests import IntegrationFixture


class TestAdd(IntegrationFixture):

    def setUp(self):
        super(TestAdd, self).setUp()
        # Use permissive since we're using functional tests for permissions
        self.config.testing_securitypolicy(userid='joe', permissive=True)
        from occams.studies.views.export import add
        self.view_func = add

    def test_get_exportables(self):
        """
        It should render only published schemata
        """
        from occams.studies.security import track_user

        track_user('joe')

        # No schemata
        request = testing.DummyRequest(
            layout_manager=mock.Mock())
        response = self.view_func(request)
        self.assertEquals(len(response['exportables']), 4)  # Only pre-cooked

        # Not-yet-published schemata
        schema = models.Schema(
            name=u'vitals', title=u'Vitals')
        Session.add(schema)
        Session.flush()
        request = testing.DummyRequest(
            layout_manager=mock.Mock())
        response = self.view_func(request)
        self.assertEquals(len(response['exportables']), 4)

        # Published schemata
        schema.publish_date = date.today()
        Session.flush()
        request = testing.DummyRequest(
            layout_manager=mock.Mock())
        response = self.view_func(request)
        self.assertEquals(len(response['exportables']), 5)

    def test_post_empty(self):
        """
        It should raise validation errors on empty imput
        """
        request = testing.DummyRequest(
            layout_manager=mock.Mock(),
            post=MultiDict())
        response = self.view_func(request)
        self.assertIsNotNone(response['errors']['contents'])

    def test_post_non_existent_schema(self):
        """
        It should raise validation errors for non-existent schemata
        """
        request = testing.DummyRequest(
            layout_manager=mock.Mock(),
            post=MultiDict([('contents', 'does_not_exist')]))
        response = self.view_func(request)
        self.assertIsNotNone(response['errors']['contents'])

    def test_post_invalid_csrf(self):
        """
        It should check for cross-site forgery
        """
        request = testing.DummyRequest(
            layout_manager=mock.Mock(),
            post=MultiDict([('csrf_token', 'd3v10us')]))
        response = self.view_func(request)
        self.assertIsNotNone(response['errors']['csrf_token'])

    # Don't actually invoke the subtasks
    @mock.patch('occams.studies.tasks.make_export')
    def test_valid(self, make_export):
        """
        It should add an export record and initiate an async task
        """
        from pyramid.httpexceptions import HTTPFound
        from occams.studies.security import track_user

        self.config.include('occams.studies.routes')
        self.config.registry.settings['app.export.dir'] = '/tmp'

        track_user('joe')

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
        from occams.studies.security import track_user

        self.config.registry.settings['app.export.limit'] = 0

        track_user('joe')
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
        self.assertTrue(response['exceeded'])


class TestStatusJSON(IntegrationFixture):

    def setUp(self):
        super(TestStatusJSON, self).setUp()
        # Use permissive since we're using functional tests for permissions
        self.config.testing_securitypolicy(userid='joe', permissive=True)
        from occams.studies.views.export import status_json
        self.view_func = status_json

    def test_get_current_user(self):
        """
        It should return the authenticated user's exports
        """
        from occams.studies.security import track_user

        self.config.registry.settings['app.export.dir'] = '/tmp'
        self.config.include('occams.studies.routes')

        track_user('jane')
        track_user('joe')

        Session.add_all([
            models.Export(
                owner_user=(
                    Session.query(models.User)
                    .filter_by(key='joe')
                    .one()),
                contents=[],
                status='pending'),
            models.Export(
                owner_user=(
                    Session.query(models.User)
                    .filter_by(key='jane')
                    .one()),
                contents=[],
                status='pending')])
        Session.flush()

        request = testing.DummyRequest(
            layout_manager=mock.Mock())
        response = self.view_func(request)
        exports = response['exports']
        self.assertEquals(len(exports), 1)

    def test_ignore_expired(self):
        """
        It should not render expired exports.
        """
        from datetime import datetime, timedelta
        from occams.studies.security import track_user

        EXPIRE_DAYS = 10

        self.config.registry.settings['app.export.expire'] = EXPIRE_DAYS
        self.config.registry.settings['app.export.dir'] = '/tmp'
        self.config.include('occams.studies.routes')

        track_user('joe')

        now = datetime.now()

        export = models.Export(
            owner_user=(
                Session.query(models.User)
                .filter_by(key='joe')
                .one()),
            contents=[],
            status='pending',
            create_date=now)
        Session.add(export)
        Session.flush()

        request = testing.DummyRequest(
            layout_manager=mock.Mock())
        response = self.view_func(request)
        exports = response['exports']
        self.assertEquals(len(exports), 1)

        export.create_date = export.modify_date = \
            now - timedelta(EXPIRE_DAYS + 1)
        Session.flush()
        request = testing.DummyRequest(
            layout_manager=mock.Mock())
        response = self.view_func(request)
        exports = response['exports']
        self.assertEquals(len(exports), 0)


class TestDelete(IntegrationFixture):

    def setUp(self):
        super(TestDownload, self).setUp()
        # Use permissive since we're using functional tests for permissions
        self.config.testing_securitypolicy(userid='joe', permissive=True)
        from occams.studies.views.export import delete
        self.view_func = delete

    @mock.patch('occams.studies.occams.studies.exports.celery')
    def test_deleteable_by_owner(self, celery):
        """
        It should allow the owner of the export to cancel/delete the export
        """
        from occams.studies import models, Session
        from occams.studies.security import track_user

        track_user('joe')

        export = models.Export(
            owner_user=(
                Session.query(models.User)
                .filter_by(key='jane')
                .one()),
            contents=[],
            status='complete')
        Session.add(export)


@ddt
class TestDownload(IntegrationFixture):

    def setUp(self):
        super(TestDownload, self).setUp()
        # Use permissive since we're using functional tests for permissions
        self.config.testing_securitypolicy(userid='joe', permissive=True)
        from occams.studies.views.export import download
        self.view_func = download

    def test_get_owner_exports(self):
        """
        It should only allow owners of the export to download it
        """
        import os
        from pyramid.httpexceptions import HTTPNotFound
        from pyramid.response import FileResponse
        from occams.studies.security import track_user

        self.config.registry.settings['app.export.dir'] = '/tmp'
        track_user('joe')
        track_user('jane')
        export = models.Export(
            id=123,
            owner_user=(
                Session.query(models.User)
                .filter_by(key='jane')
                .one()),
            contents=[],
            status='complete')
        Session.add(export)
        Session.flush()

        fp = open('/tmp/' + export.name, 'w+b')

        self.config.testing_securitypolicy(userid='joe', permissive=True)
        request = testing.DummyRequest(
            layout_manager=mock.Mock(),
            matchdict={'id': 123})
        with self.assertRaises(HTTPNotFound):
            self.view_func(request)

        self.config.testing_securitypolicy(userid='jane', permissive=True)
        request = testing.DummyRequest(
            layout_manager=mock.Mock(),
            matchdict={'id': 123})
        response = self.view_func(request)
        self.assertIsInstance(response, FileResponse)

        fp.close()
        os.remove(fp.name)

    @data('failed', 'pending')
    def test_get_not_found_status(self, status):
        """
        It should return 404 if the record is not ready
        """
        from pyramid.httpexceptions import HTTPNotFound
        from occams.studies.security import track_user

        track_user('joe')
        Session.add(models.Export(
            id=123,
            owner_user=(
                Session.query(models.User)
                .filter_by(key='joe')
                .one()),
            contents=[],
            status=status))

        request = testing.DummyRequest(
            layout_manager=mock.Mock(),
            matchdict={'id': 123})
        with self.assertRaises(HTTPNotFound):
            self.view_func(request)
