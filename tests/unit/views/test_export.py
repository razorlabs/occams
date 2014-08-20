from ddt import ddt, data
import mock

from tests import IntegrationFixture


class TestAdd(IntegrationFixture):

    def call_view(self, request):
        from occams.studies.views.export import add as view
        return view(request)

    def test_get_exportables(self):
        """
        It should render only published schemata
        """
        from datetime import date
        from pyramid import testing
        from tests import track_user
        from occams.studies import Session, models

        track_user('joe')

        # No schemata
        request = testing.DummyRequest()
        response = self.call_view(request)
        self.assertEquals(len(response['exportables']), 3)  # Only pre-cooked

        # Not-yet-published schemata
        schema = models.Schema(
            name=u'vitals', title=u'Vitals')
        Session.add(schema)
        Session.flush()
        request = testing.DummyRequest()
        response = self.call_view(request)
        self.assertEquals(len(response['exportables']), 3)

        # Published schemata
        schema.publish_date = date.today()
        Session.flush()
        request = testing.DummyRequest()
        response = self.call_view(request)
        self.assertEquals(len(response['exportables']), 4)

    @mock.patch('occams.studies.views.export.check_csrf_token')
    def test_post_empty(self, check_csrf_token):
        """
        It should raise validation errors on empty imput
        """
        from pyramid import testing
        from webob.multidict import MultiDict
        request = testing.DummyRequest(post=MultiDict())
        response = self.call_view(request)
        self.assertIsNotNone(response['errors'])

    @mock.patch('occams.studies.views.export.check_csrf_token')
    def test_post_non_existent_schema(self, check_csrf_token):
        """
        It should raise validation errors for non-existent schemata
        """
        from pyramid import testing
        from webob.multidict import MultiDict
        request = testing.DummyRequest(
            post=MultiDict([('contents', 'does_not_exist')]))
        response = self.call_view(request)
        self.assertIn('Invalid selection', response['errors'][0])

    @mock.patch('occams.studies.views.export.check_csrf_token')
    @mock.patch('occams.studies.tasks.make_export')  # Don't invoke subtasks
    def test_valid(self, make_export, check_csrf_token):
        """
        It should add an export record and initiate an async task
        """
        from datetime import date
        from pyramid import testing
        from pyramid.httpexceptions import HTTPFound
        from webob.multidict import MultiDict
        from tests import track_user
        from occams.studies import Session, models

        self.config.include('occams.studies.routes')
        self.config.add_route('export_status', '/dummy')
        self.config.registry.settings['app.export.dir'] = '/tmp'

        track_user('joe')

        schema = models.Schema(
            name=u'vitals', title=u'Vitals', publish_date=date.today())
        Session.add(schema)
        Session.flush()

        self.config.testing_securitypolicy(userid='joe')
        request = testing.DummyRequest(
            post=MultiDict([
                ('contents', str('vitals'))
            ]))

        response = self.call_view(request)
        check_csrf_token.assert_called_with(request)
        self.assertIsInstance(response, HTTPFound)
        self.assertEqual(response.location,
                         request.route_path('export_status'))
        export = Session.query(models.Export).one()
        self.assertEqual(export.owner_user.key, 'joe')

    @mock.patch('occams.studies.views.export.check_csrf_token')
    def test_exceed_limit(self, check_csrf_token):
        """
        It should not let the user exceed their allocated export limit
        """
        from datetime import date
        from pyramid import testing
        from webob.multidict import MultiDict
        from tests import track_user
        from occams.studies import Session, models

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
        self.config.testing_securitypolicy(userid='joe')
        request = testing.DummyRequest()
        response = self.call_view(request)
        self.assertTrue(response['exceeded'])

        # If the user insists, they'll get a validation error as well
        self.config.testing_securitypolicy(userid='joe')
        request = testing.DummyRequest(
            post=MultiDict([
                ('contents', 'vitals')
                ]))
        self.assertTrue(response['exceeded'])


class TestStatusJSON(IntegrationFixture):

    def call_view(self, request):
        from occams.studies.views.export import status_json as view
        return view(request)

    def test_get_current_user(self):
        """
        It should return the authenticated user's exports
        """
        from pyramid import testing
        from tests import track_user
        from occams.studies import Session, models

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

        self.config.testing_securitypolicy(userid='joe')
        request = testing.DummyRequest()
        response = self.call_view(request)
        exports = response['exports']
        self.assertEquals(len(exports), 1)

    def test_ignore_expired(self):
        """
        It should not render expired exports.
        """
        from datetime import datetime, timedelta
        from pyramid import testing
        from tests import track_user
        from occams.studies import Session, models

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
            create_date=now,
            modify_date=now)
        Session.add(export)
        Session.flush()

        self.config.testing_securitypolicy(userid='joe')
        request = testing.DummyRequest()
        response = self.call_view(request)
        exports = response['exports']
        self.assertEquals(len(exports), 1)

        export.create_date = export.modify_date = \
            now - timedelta(EXPIRE_DAYS + 1)
        Session.flush()
        request = testing.DummyRequest()
        response = self.call_view(request)
        exports = response['exports']
        self.assertEquals(len(exports), 0)


class TestCodebookJSON(IntegrationFixture):

    def call_view(self, request):
        from occams.studies.views.export import codebook_json as view
        return view(request)

    def test_file_not_specified(self):
        """
        It should return 404 if the file not specified
        """
        from pyramid import testing
        from pyramid.httpexceptions import HTTPNotFound
        from webob.multidict import MultiDict

        request = testing.DummyRequest(
            params=MultiDict([('file', '')])
        )

        with self.assertRaises(HTTPNotFound):
            self.call_view(request)

    def test_file_not_exists(self):
        """
        It should return 404 if the file does not exist
        """
        from pyramid import testing
        from pyramid.httpexceptions import HTTPNotFound
        from webob.multidict import MultiDict

        request = testing.DummyRequest(
            params=MultiDict([('file', 'i_dont_exist')])
        )

        with self.assertRaises(HTTPNotFound):
            self.call_view(request)

    def test_file(self):
        """
        It should return the json rows for the codebook fragment
        """
        from datetime import date
        from pyramid import testing
        from webob.multidict import MultiDict
        from occams.studies import Session, models
        from tests import track_user

        track_user('joe')

        Session.add(models.Schema(
            name=u'aform',
            title=u'',
            publish_date=date.today(),
            attributes={
                u'myfield': models.Attribute(
                    name=u'myfield',
                    title=u'',
                    type=u'string',
                    order=0
                    )
            }
        ))
        Session.flush()

        request = testing.DummyRequest(
            params=MultiDict([('file', 'aform')])
        )

        response = self.call_view(request)
        self.assertIsNotNone(response)


class TestCodebookDownload(IntegrationFixture):

    def call_view(self, request):
        from occams.studies.views.export import codebook_download as view
        return view(request)

    def test_download(self):
        """
        It should allow downloading of entire codebook file
        """
        import os
        from pyramid import testing
        from pyramid.response import FileResponse
        from occams.studies.exports.codebook import FILE_NAME
        self.config.registry.settings['app.export.dir'] = '/tmp'
        name = '/tmp/' + FILE_NAME
        with open(name, 'w+b'):
            self.config.testing_securitypolicy(userid='jane')
            request = testing.DummyRequest()
            response = self.call_view(request)
            self.assertIsInstance(response, FileResponse)
        os.remove(name)


class TestDelete(IntegrationFixture):

    def call_view(self, request):
        from occams.studies.views.export import delete as view
        return view(request)

    @mock.patch('occams.studies.views.export.check_csrf_token')
    @mock.patch('occams.studies.tasks.celery.control.revoke')
    def test_deletable_not_owner(self, revoke, check_csrf_token):
        """
        It should issue a 404 if the user does not own the export
        """
        from pyramid import testing
        from pyramid.httpexceptions import HTTPNotFound
        from occams.studies import models, Session
        from tests import track_user

        track_user('jane', is_current=False)
        track_user('joe')

        export = models.Export(
            owner_user=(
                Session.query(models.User)
                .filter_by(key='jane')
                .one()),
            contents=[],
            status='complete')
        Session.add(export)
        Session.flush()
        export_id = export.id
        Session.expunge_all()

        request = testing.DummyRequest(
            matchdict={'export': str(export_id)})

        with self.assertRaises(HTTPNotFound):
            self.call_view(request)

    @mock.patch('occams.studies.views.export.check_csrf_token')
    @mock.patch('occams.studies.tasks.celery.control.revoke')
    def test_not_found(self, revoke, check_csrf_token):
        """
        It should issue a 404 if the export does not exist
        """
        from pyramid import testing
        from pyramid.httpexceptions import HTTPNotFound

        request = testing.DummyRequest(
            matchdict={'export': str('123')})

        with self.assertRaises(HTTPNotFound):
            self.call_view(request)

    @mock.patch('occams.studies.views.export.check_csrf_token')
    @mock.patch('occams.studies.tasks.celery.control.revoke')
    def test_deleteable_by_owner(self, revoke, check_csrf_token):
        """
        It should allow the owner of the export to cancel/delete the export
        """
        from pyramid import testing
        from pyramid.httpexceptions import HTTPOk
        from occams.studies import models, Session
        from tests import track_user

        track_user('joe')

        export = models.Export(
            owner_user=(
                Session.query(models.User)
                .filter_by(key='joe')
                .one()),
            contents=[],
            status='complete')
        Session.add(export)
        Session.flush()
        export_id = export.id
        export_name = export.name
        Session.expunge_all()

        self.config.testing_securitypolicy(userid='joe')
        request = testing.DummyRequest(
            matchdict={'export': str(export_id)})
        response = self.call_view(request)
        check_csrf_token.assert_called_with(request)
        self.assertIsInstance(response, HTTPOk)
        self.assertIsNone(Session.query(models.Export).get(export_id))
        revoke.assert_called_with(export_name)


@ddt
class TestDownload(IntegrationFixture):

    def call_view(self, request):
        from occams.studies.views.export import download as view
        return view(request)

    def test_get_owner_exports(self):
        """
        It should only allow owners of the export to download it
        """
        import os
        from pyramid import testing
        from pyramid.httpexceptions import HTTPNotFound
        from pyramid.response import FileResponse
        from tests import track_user
        from occams.studies import Session, models

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

        name = '/tmp/' + export.name
        with open(name, 'w+b'):
            request = testing.DummyRequest(
                matchdict={'export': 123})
            with self.assertRaises(HTTPNotFound):
                self.call_view(request)

            self.config.testing_securitypolicy(userid='jane')
            request = testing.DummyRequest(
                matchdict={'export': 123})
            response = self.call_view(request)
            self.assertIsInstance(response, FileResponse)
        os.remove(name)

    @data('failed', 'pending')
    def test_get_not_found_status(self, status):
        """
        It should return 404 if the record is not ready
        """
        from pyramid import testing
        from pyramid.httpexceptions import HTTPNotFound
        from tests import track_user
        from occams.studies import Session, models

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
            matchdict={'export': 123})
        with self.assertRaises(HTTPNotFound):
            self.call_view(request)
