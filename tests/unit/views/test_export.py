import pytest


@pytest.yield_fixture
def check_csrf_token(config):
    import mock
    name = 'occams_studies.views.export.check_csrf_token'
    with mock.patch(name) as patch:
        yield patch


class TestAdd:

    def _call_fut(self, *args, **kw):
        from occams_studies.views.export import checkout as view
        return view(*args, **kw)

    def test_get_exportables(self, req, db_session):
        """
        It should render only published schemata
        """
        from datetime import date
        from occams_studies import models
        from occams_studies.exports.schema import SchemaPlan

        req.registry.settings['studies.export.plans'] = [SchemaPlan.list_all]

        # No schemata
        res = self._call_fut(models.ExportFactory(req), req)
        assert len(res['exportables']) == 0  # Only pre-cooked

        # Not-yet-published schemata
        schema = models.Schema(
            name=u'vitals', title=u'Vitals')
        db_session.add(schema)
        db_session.flush()
        res = self._call_fut(models.ExportFactory(req), req)
        assert len(res['exportables']) == 0

        # Published schemata
        schema.publish_date = date.today()
        db_session.flush()
        res = self._call_fut(models.ExportFactory(req), req)
        assert len(res['exportables']) == 1

    def test_post_empty(self, req, db_session):
        """
        It should raise validation errors on empty imput
        """
        from webob.multidict import MultiDict
        from occams_studies import models
        from occams_studies.exports.schema import SchemaPlan
        req.registry.settings['studies.export.plans'] = [SchemaPlan.list_all]
        req.method = 'POST'
        req.POST = MultiDict()
        res = self._call_fut(models.ExportFactory(req), req)
        assert res['errors'] is not None

    def test_post_non_existent_schema(self, req, db_session, config):
        """
        It should raise validation errors for non-existent schemata
        """
        from webob.multidict import MultiDict
        from occams_studies import models
        from occams_studies.exports.schema import SchemaPlan
        config.testing_securitypolicy(userid='tester', permissive=True)
        req.registry.settings['studies.export.plans'] = [SchemaPlan.list_all]
        req.method = 'POST'
        req.POST = MultiDict([('contents', 'does_not_exist')])
        res = self._call_fut(models.ExportFactory(req), req)
        assert 'not a valid choice' in res['errors']['contents']

    def test_valid(self, req, db_session, config, check_csrf_token):
        """
        It should add an export record and initiate an async task
        """
        from datetime import date
        import mock
        from pyramid.httpexceptions import HTTPFound
        from webob.multidict import MultiDict
        from occams_studies import models
        from occams_studies.exports.schema import SchemaPlan

        req.registry.settings['app.export.dir'] = '/tmp'
        req.registry.settings['studies.export.plans'] = [SchemaPlan.list_all]

        blame = models.User(key=u'joe')
        db_session.add(blame)
        db_session.flush()
        db_session.info['blame'] = blame

        schema = models.Schema(
            name=u'vitals', title=u'Vitals', publish_date=date.today())
        db_session.add(schema)
        db_session.flush()

        config.testing_securitypolicy(userid='joe')
        req.method = 'POST'
        req.POST = MultiDict([('contents', str('vitals'))])

        # Don't invoke subtasks
        with mock.patch('occams_studies.tasks.make_export'):
            res = self._call_fut(models.ExportFactory(req), req)

        check_csrf_token.assert_called_with(req)
        assert isinstance(res, HTTPFound)
        assert res.location == req.route_path('studies.exports_status')
        export = db_session.query(models.Export).one()
        assert export.owner_user.key == 'joe'

    def test_exceed_limit(self, req, db_session, config):
        """
        It should not let the user exceed their allocated export limit
        """
        from datetime import date
        from webob.multidict import MultiDict
        from occams_studies import models
        from occams_studies.exports.schema import SchemaPlan

        config.registry.settings['app.export.limit'] = 0
        req.registry.settings['studies.export.plans'] = [SchemaPlan.list_all]

        blame = models.User(key=u'joe')
        db_session.add(blame)
        db_session.flush()
        db_session.info['blame'] = blame

        previous_export = models.Export(
            owner_user=(
                db_session.query(models.User)
                .filter_by(key='joe')
                .one()),
            contents=[{
                u'name': u'vitals',
                u'title': u'Vitals',
                u'versions': [str(date.today())]}])
        db_session.add(previous_export)
        db_session.flush()

        # The renderer should know about it
        config.testing_securitypolicy(userid='joe')
        res = self._call_fut(models.ExportFactory(req), req)
        assert res['exceeded']

        # If the user insists, they'll get a validation error as well
        config.testing_securitypolicy(userid='joe')
        req.method = 'POST'
        req.POST = MultiDict([('contents', 'vitals')])
        assert res['exceeded']


class TestStatusJSON:

    def _call_fut(self, *args, **kw):
        from occams_studies.views.export import status_json as view
        return view(*args, **kw)

    def test_get_current_user(self, req, db_session, config):
        """
        It should return the authenticated user's exports
        """
        import mock
        from occams_studies import models

        req.registry.settings['studies.export.dir'] = '/tmp'

        blame = models.User(key=u'joe')
        db_session.add(blame)
        db_session.add(models.User(key='jane'))
        db_session.flush()
        db_session.info['blame'] = blame

        export1 = models.Export(
            owner_user=(
                db_session.query(models.User)
                .filter_by(key='joe')
                .one()),
            contents=[],
            status='pending')
        export2 = models.Export(
            owner_user=(
                db_session.query(models.User)
                .filter_by(key='jane')
                .one()),
            contents=[],
            status='pending')
        db_session.add_all([export1, export2])
        db_session.flush()

        config.testing_securitypolicy(userid='joe')
        req.redis = mock.Mock()
        context = models.ExportFactory(req)
        export1.__parent__ = context
        export2.__parent__ = context
        res = self._call_fut(models.ExportFactory(req), req)
        exports = res['exports']
        assert len(exports) == 1

    def test_ignore_expired(self, req, db_session, config):
        """
        It should not render expired exports.
        """
        from datetime import datetime, timedelta
        import mock
        from occams_studies import models

        EXPIRE_DAYS = 10

        req.registry.settings['studies.export.expire'] = EXPIRE_DAYS
        req.registry.settings['studies.export.dir'] = '/tmp'

        blame = models.User(key=u'joe')
        db_session.add(blame)
        db_session.flush()
        db_session.info['blame'] = blame

        now = datetime.now()

        export = models.Export(
            owner_user=(
                db_session.query(models.User)
                .filter_by(key='joe')
                .one()),
            contents=[],
            status='pending',
            create_date=now,
            modify_date=now)
        db_session.add(export)
        db_session.flush()

        config.testing_securitypolicy(userid='joe')
        req.redis = mock.Mock()
        context = models.ExportFactory(req)
        export.__parent__ = context
        res = self._call_fut(context, req)
        exports = res['exports']
        assert len(exports) == 1

        export.create_date = export.modify_date = \
            now - timedelta(EXPIRE_DAYS + 1)
        db_session.flush()
        context = models.ExportFactory(req)
        export.__parent__ = context
        res = self._call_fut(context, req)
        exports = res['exports']
        assert len(exports) == 0


class TestNotifications:

    def _call_fut(self, *args, **kw):
        from occams_studies.views.export import notifications
        return notifications(*args, **kw)

    def test_ignore_nonmessages(self, req, db_session, config):
        """
        It should not yield other types of pubsub broadcasts
        """
        import mock
        from occams_studies import models

        def listen():
            return [{
                'type': 'misc',
                'data': 'random data'
            }]

        req.redis = mock.Mock(pubsub=lambda: mock.Mock(listen=listen))

        res = self._call_fut(models.ExportFactory(req), req)

        notifications = list(res.app_iter)

        assert not notifications

    def test_ignore_nonowner(self, req, db_session, config):
        """
        It should not yield pubsub "message" broadcasts if they
        don't belong to the autheticated user.
        """
        import json
        import mock
        from occams_studies import models

        config.testing_securitypolicy(userid='somoneelse')

        def listen():
            return [{
                'type': 'message',
                'data': json.dumps({'owner_user': 'jane', 'export_id': 123})
            }]

        req.redis = mock.Mock(pubsub=lambda: mock.Mock(listen=listen))

        res = self._call_fut(models.ExportFactory(req), req)

        notifications = list(res.app_iter)

        assert not notifications

    def test_yield_pubsub_owner_messages(self, req, db_session, config):
        """
        It should only yield pubsub "message" broadcasts to the owner
        """
        import json
        import mock
        from occams_studies import models

        config.testing_securitypolicy(userid='jane')

        def listen():
            return [{
                'type': 'message',
                'data': json.dumps({'owner_user': 'jane', 'export_id': 123})
            }]

        req.redis = mock.Mock(pubsub=lambda: mock.Mock(listen=listen))

        res = self._call_fut(models.ExportFactory(req), req)

        notifications = list(res.app_iter)

        assert notifications
        assert '"export_id": 123' in notifications[0]


class TestCodebookJSON:

    def _call_fut(self, *args, **kw):
        from occams_studies.views.export import codebook_json as view
        return view(*args, **kw)

    def test_file_not_specified(self, req, db_session):
        """
        It should return 404 if the file not specified
        """
        from pyramid.httpexceptions import HTTPBadRequest
        from webob.multidict import MultiDict
        import pytest
        from occams_studies import models
        from occams_studies.exports.schema import SchemaPlan

        req.GET = MultiDict([('file', '')])
        req.registry.settings['studies.export.plans'] = [SchemaPlan.list_all]

        with pytest.raises(HTTPBadRequest):
            self._call_fut(models.ExportFactory(req), req)

    def test_file_not_exists(self, req, db_session):
        """
        It should return 404 if the file does not exist
        """
        from pyramid.httpexceptions import HTTPBadRequest
        from webob.multidict import MultiDict
        import pytest
        from occams_studies import models
        from occams_studies.exports.schema import SchemaPlan

        req.GET = MultiDict([('file', 'i_dont_exist')])
        req.registry.settings['studies.export.plans'] = [SchemaPlan.list_all]

        with pytest.raises(HTTPBadRequest):
            self._call_fut(models.ExportFactory(req), req)

    def test_file(self, req, db_session):
        """
        It should return the json rows for the codebook fragment
        """
        from datetime import date
        from webob.multidict import MultiDict
        from occams_studies import models
        from occams_studies.exports.schema import SchemaPlan

        db_session.add(models.Schema(
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
        db_session.flush()

        req.GET = MultiDict([('file', 'aform')])
        req.registry.settings['studies.export.plans'] = [SchemaPlan.list_all]
        res = self._call_fut(models.ExportFactory(req), req)
        assert res is not None


class TestCodebookDownload:

    def _call_fut(self, *args, **kw):
        from occams_studies.views.export import codebook_download as view
        return view(*args, **kw)

    def test_download(self, req, db_session, config):
        """
        It should allow downloading of entire codebook file
        """
        import os
        from pyramid.response import FileResponse
        from occams_studies.exports.codebook import FILE_NAME
        from occams_studies import models
        req.registry.settings['studies.export.dir'] = '/tmp'
        name = '/tmp/' + FILE_NAME
        with open(name, 'w+b'):
            config.testing_securitypolicy(userid='jane')
            res = self._call_fut(models.ExportFactory(req), req)
            assert isinstance(res, FileResponse)
        os.remove(name)


class TestDelete:

    def _call_fut(self, *args, **kw):
        from occams_studies.views.export import delete_json as view
        return view(*args, **kw)

    def test_delete(self, req, db_session, config, check_csrf_token):
        """
        It should allow the owner of the export to cancel/delete the export
        """
        import mock
        from pyramid.httpexceptions import HTTPOk
        from occams_studies import models

        blame = models.User(key=u'joe')
        db_session.add(blame)
        db_session.flush()
        db_session.info['blame'] = blame

        export = models.Export(
            owner_user=(
                db_session.query(models.User)
                .filter_by(key='joe')
                .one()),
            contents=[],
            status='complete')
        db_session.add(export)
        db_session.flush()
        export_id = export.id
        export_name = export.name
        db_session.expunge_all()

        config.testing_securitypolicy(userid='joe')
        with mock.patch('occams_studies.tasks.app.control.revoke') as revoke:
            res = self._call_fut(export, req)
        check_csrf_token.assert_called_with(req)
        assert isinstance(res, HTTPOk)
        assert db_session.query(models.Export).get(export_id) is None
        revoke.assert_called_with(export_name)


class TestDownload:

    def _call_fut(self, *args, **kw):
        from occams_studies.views.export import download as view
        return view(*args, **kw)

    @pytest.mark.parametrize('status', ['failed', 'pending'])
    def test_get_not_found_status(self, req, db_session, status):
        """
        It should return 404 if the record is not ready
        """
        from pyramid.httpexceptions import HTTPBadRequest
        from occams_studies import models

        blame = models.User(key=u'joe')
        db_session.add(blame)
        db_session.flush()
        db_session.info['blame'] = blame

        export = models.Export(
            id=123,
            owner_user=(
                db_session.query(models.User)
                .filter_by(key='joe')
                .one()),
            contents=[],
            status=status)
        db_session.add(export)
        db_session.flush()

        with pytest.raises(HTTPBadRequest):
            self._call_fut(export, req)
