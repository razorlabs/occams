from ddt import ddt, data
import mock

from tests import IntegrationFixture


class TestAdd(IntegrationFixture):

    @property
    def view_func(self):
        from occams.studies.views.export import add
        return add

    def test_get_exportables(self):
        """
        It should render only published schemata
        """
        from datetime import date
        from pyramid import testing
        from tests import track_user
        from occams.studies import Session, models

        #self.config.testing_securitypolicy(userid='joe', permissive=True)
        track_user('joe')

        # No schemata
        request = testing.DummyRequest()
        response = self.view_func(request)
        self.assertEquals(len(response['exportables']), 4)  # Only pre-cooked

        # Not-yet-published schemata
        schema = models.Schema(
            name=u'vitals', title=u'Vitals')
        Session.add(schema)
        Session.flush()
        request = testing.DummyRequest()
        response = self.view_func(request)
        self.assertEquals(len(response['exportables']), 4)

        # Published schemata
        schema.publish_date = date.today()
        Session.flush()
        request = testing.DummyRequest()
        response = self.view_func(request)
        self.assertEquals(len(response['exportables']), 5)

    def test_post_empty(self):
        """
        It should raise validation errors on empty imput
        """
        from pyramid import testing
        from webob.multidict import MultiDict
        request = testing.DummyRequest(
            post=MultiDict())
        response = self.view_func(request)
        self.assertIsNotNone(response['errors']['contents'])

    def test_post_non_existent_schema(self):
        """
        It should raise validation errors for non-existent schemata
        """
        from pyramid import testing
        from webob.multidict import MultiDict
        request = testing.DummyRequest(
            post=MultiDict([('contents', 'does_not_exist')]))
        response = self.view_func(request)
        self.assertIsNotNone(response['errors']['contents'])

    def test_post_invalid_csrf(self):
        """
        It should check for cross-site forgery
        """
        from pyramid import testing
        from webob.multidict import MultiDict
        request = testing.DummyRequest(
            post=MultiDict([('csrf_token', 'd3v10us')]))
        response = self.view_func(request)
        self.assertIsNotNone(response['errors']['csrf_token'])

    # Don't actually invoke the subtasks
    @mock.patch('occams.studies.tasks.make_export')
    def test_valid(self, make_export):
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
        response = self.view_func(request)
        self.assertTrue(response['exceeded'])

        # If the user insists, they'll get a validation error as well
        self.config.testing_securitypolicy(userid='joe')
        request = testing.DummyRequest(
            post=MultiDict([
                ('contents', 'vitals')
                ]))
        request.POST['csrf_token'] = request.session.get_csrf_token()
        self.assertTrue(response['exceeded'])


class TestStatusJSON(IntegrationFixture):

    @property
    def view_func(self):
        from occams.studies.views.export import status_json
        return status_json

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
        response = self.view_func(request)
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
        response = self.view_func(request)
        exports = response['exports']
        self.assertEquals(len(exports), 1)

        export.create_date = export.modify_date = \
            now - timedelta(EXPIRE_DAYS + 1)
        Session.flush()
        request = testing.DummyRequest()
        response = self.view_func(request)
        exports = response['exports']
        self.assertEquals(len(exports), 0)


class TestCodebookJSON(IntegrationFixture):

    @property
    def view_func(self):
        from occams.studies.views.export import codebook_json
        return codebook_json

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
            self.view_func(request)

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
            self.view_func(request)

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

        response = self.view_func(request)
        self.assertIsNotNone(response)


class TestCodebookDownload(IntegrationFixture):

    @property
    def view_func(self):
        from occams.studies.views.export import codebook_download
        return codebook_download

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
            response = self.view_func(request)
            self.assertIsInstance(response, FileResponse)
        os.remove(name)


class TestDelete(IntegrationFixture):

    @property
    def view_func(self):
        from occams.studies.views.export import delete
        return delete

    @mock.patch('occams.studies.tasks.celery.control.revoke')
    def test_deletable_not_owner(self, revoke):
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
            matchdict={'id': str(export_id)})
        request.POST['csrf_token'] = request.session.get_csrf_token()

        with self.assertRaises(HTTPNotFound):
            self.view_func(request)

    @mock.patch('occams.studies.tasks.celery.control.revoke')
    def test_not_found(self, revoke):
        """
        It should issue a 404 if the export does not exist
        """
        from pyramid import testing
        from pyramid.httpexceptions import HTTPNotFound

        request = testing.DummyRequest(
            matchdict={'id': str('123')})
        request.POST['csrf_token'] = request.session.get_csrf_token()

        with self.assertRaises(HTTPNotFound):
            self.view_func(request)

    @mock.patch('occams.studies.tasks.celery.control.revoke')
    def test_invalid_csrf(self, revoke):
        """
        It should deny invalid CSRF tokens
        """
        from pyramid import testing
        from pyramid.httpexceptions import HTTPForbidden
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
        Session.expunge_all()

        self.config.testing_securitypolicy(userid='joe')
        request = testing.DummyRequest(
            matchdict={'id': str(export_id)})
        request.POST['csrf_token'] = 'd3v10us'

        with self.assertRaises(HTTPForbidden):
            self.view_func(request)

    @mock.patch('occams.studies.tasks.celery.control.revoke')
    def test_deleteable_by_owner(self, revoke):
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
            matchdict={'id': str(export_id)})
        request.POST['csrf_token'] = request.session.get_csrf_token()

        response = self.view_func(request)
        self.assertIsInstance(response, HTTPOk)
        self.assertIsNone(Session.query(models.Export).get(export_id))
        revoke.assert_called_with(export_name)


@ddt
class TestDownload(IntegrationFixture):

    @property
    def view_func(self):
        from occams.studies.views.export import download
        return download

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
                matchdict={'id': 123})
            with self.assertRaises(HTTPNotFound):
                self.view_func(request)

            self.config.testing_securitypolicy(userid='jane')
            request = testing.DummyRequest(
                matchdict={'id': 123})
            response = self.view_func(request)
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
            matchdict={'id': 123})
        with self.assertRaises(HTTPNotFound):
            self.view_func(request)
