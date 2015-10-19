import pytest

from occams.testing import USERID, make_environ, get_csrf_token


class TestPermissionForms:
    ALL_ALLOWED = ('administrator', 'manager', 'editor', None)
    DEFAULT_ALLOWED = ('administrator', 'manager', 'editor')
    DEFAULT_NOT_ALLOWED = ('enterer', 'reviewer', 'member')
    ALLOWED_NO_EDITOR = ('administrator', 'manager')
    NOT_ALLOWED_W_EDITOR = ('editor', 'enterer', 'reviewer', 'member')

    @pytest.fixture(autouse=True)
    def populate(self, db_session):
        from datetime import date
        import transaction
        from occams_datastore import models as datastore

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            db_session.info['blame'] = user
            db_session.add(user)
            db_session.flush()

            form_published = datastore.Schema(
                name=u'test_schema',
                title=u'test_title',
                publish_date=date(2015, 1, 1)
            )

            form_unpublished = datastore.Schema(
                name=u'test_schema2',
                title=u'test_title2',
            )

            db_session.add(datastore.Attribute(
                name=u'test_field',
                title=u'test_title',
                description=u'test_desc',
                type=u'string',
                schema=form_published,
                order=0
            ))

            db_session.add(datastore.Attribute(
                name=u'text_box2',
                title=u'text_box2',
                description=u'text_box_desc2',
                type=u'string',
                schema=form_published,
                order=1
            ))

            db_session.add(datastore.Attribute(
                name=u'test_field2',
                title=u'test_title2',
                description=u'test_desc2',
                type=u'string',
                schema=form_unpublished,
                order=0
            ))

            db_session.add(datastore.Attribute(
                name=u'text_box2',
                title=u'text_box2',
                description=u'text_box_desc2',
                type=u'string',
                schema=form_unpublished,
                order=1
            ))

            db_session.flush()

    # tests for forms

    @pytest.mark.parametrize('group', ALL_ALLOWED)
    def test_forms_view(self, app, db_session, group):
        url = '/forms'

        environ = make_environ(userid=USERID, groups=[group])
        res = app.get(url, extra_environ=environ)
        assert 200 == res.status_code

    def test_not_authenticated_forms(self, app, db_session):
        url = '/forms'
        res = app.get(url, status='*')
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', ALL_ALLOWED)
    def test_forms_view_xhr(self, app, db_session, group):
        url = '/forms'

        environ = make_environ(userid=USERID, groups=[group])
        res = app.get(url, extra_environ=environ, xhr=True)
        assert 200 == res.status_code

    def test_not_authenticated_forms_xhr(self, app, db_session):
        url = '/forms'
        res = app.get(url, status='*', xhr=True)
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_ALLOWED)
    def test_forms_upload_json(self, app, db_session, group):
        import json

        url = '/forms?files'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        data = {
            'title': 'OMG',
            'storage': 'eav',
            'publish_date': '2015-05-26',
            "name": 'omg'
        }

        res = app.post(
            url,
            extra_environ=environ,
            status='*',
            upload_files=[('files', 'upload.json', json.dumps(data))],
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_NOT_ALLOWED)
    def test_not_allowed_forms_upload_json(self, app, db_session, group):
        import json

        url = '/forms?files'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        data = {
            'title': 'OMG',
            'storage': 'eav',
            'publish_date': '2015-05-26',
            "name": 'omg'
        }

        res = app.post(
            url,
            extra_environ=environ,
            status='*',
            upload_files=[('files', 'upload.json', json.dumps(data))],
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True)

        assert 403 == res.status_code

    def test_not_authenticated_files_upload(self, app, db_session):
        url = '/forms?files'
        res = app.post(url, status='*', xhr=True)
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_ALLOWED)
    def test_forms_add_json_validate(self, app, db_session, group):
        url = '/forms?validate'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        data = {
            'name': u'test_form',
            'title': u'test_form',
            'versions': [],
            'isNew': True,
            'hasVersions': False
        }

        res = app.get(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True,
            params=data)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_NOT_ALLOWED)
    def test_not_allowed_forms_add_json_validate(self, app, db_session, group):
        url = '/forms?validate'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        data = {
            'name': u'test_form',
            'title': u'test_form',
            'versions': [],
            'isNew': True,
            'hasVersions': False
        }

        res = app.get(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True,
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated_validate_field(self, app, db_session):
        url = '/forms?validate'

        res = app.get(url, status='*', xhr=True)
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_ALLOWED)
    def test_forms_add(self, app, db_session, group):
        url = '/forms'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        data = {
            'name': 'test_form',
            'title': 'test_form',
            'versions': [],
            'isNew': True,
            'hasVersions': False
        }

        res = app.post_json(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_NOT_ALLOWED)
    def test_not_allowed_forms_add(self, app, db_session, group):
        url = '/forms'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        data = {
            'name': 'test_form',
            'title': 'test_form',
            'versions': [],
            'isNew': True,
            'hasVersions': False
        }

        res = app.post_json(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated_forms_add(self, app, db_session):
        url = '/forms'
        res = app.post_json(url, status='*')
        assert 401 == res.status_code

    # tests for workflows

    @pytest.mark.parametrize('group', ALL_ALLOWED)
    def test_forms_workflows(self, app, db_session, group):
        url = '/forms/workflows/default'

        environ = make_environ(userid=USERID, groups=[group])
        res = app.get(url, extra_environ=environ)
        assert 200 == res.status_code

    def test_not_authenticated_workflows_default(self, app, db_session):
        url = '/forms/workflows/default'
        res = app.get(url, status='*')
        assert 401 == res.status_code

    # test for versions

    @pytest.mark.parametrize('group', ALL_ALLOWED)
    def test_forms_versions(self, app, db_session, group):
        url = '/forms/test_schema/versions/2015-01-01'

        environ = make_environ(userid=USERID, groups=[group])
        res = app.get(url, extra_environ=environ)
        assert 200 == res.status_code

    def test_not_authenticated_versions(self, app, db_session):
        url = '/forms/test_schema/versions/2015-01-01'
        res = app.get(url, status='*')
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', ALL_ALLOWED)
    def test_forms_versions_xhr(self, app, db_session, group):
        # test same url with xhr
        url = '/forms/test_schema/versions/2015-01-01'

        environ = make_environ(userid=USERID, groups=[group])
        res = app.get(url, extra_environ=environ, xhr=True)
        assert 200 == res.status_code

    def test_not_authenticated_versions_xhr(self, app, db_session):
        url = '/forms/test_schema/versions/2015-01-01'
        res = app.get(url, status='*', xhr=True)
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', ALL_ALLOWED)
    def test_forms_versions_download_json(self, app, db_session, group):
        url = '/forms/test_schema/versions/2015-01-01?download=json'

        environ = make_environ(userid=USERID, groups=[group])
        res = app.get(url, extra_environ=environ)
        assert 200 == res.status_code

    def test_not_authenticated_versions_download_json(self, app, db_session):
        url = '/forms/test_schema/versions/2015-01-01?download=json'
        res = app.get(url, status='*')
        assert 401 == res.status_code

    # tests for versions preview

    @pytest.mark.parametrize('group', ALL_ALLOWED)
    def test_forms_versions_preview(self, app, db_session, group):
        url = '/forms/test_schema/versions/2015-01-01/preview'

        environ = make_environ(userid=USERID, groups=[group])
        res = app.get(url, extra_environ=environ)
        assert 200 == res.status_code

    def test_not_authenticated_preview(self, app, db_session):
        url = '/forms/test_schema/versions/2015-01-01/preview'
        res = app.get(url, status='*')
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', ALL_ALLOWED)
    def test_forms_versions_preview_post(self, app, db_session, group):
        url = '/forms/test_schema/versions/2015-01-01/preview'

        data = {}

        environ = make_environ(userid=USERID, groups=[group])
        res = app.post(
            url,
            extra_environ=environ,
            status='*',
            params=data)

        assert 200 == res.status_code

    def test_not_authenticated_preview_post(self, app, db_session):
        url = '/forms/test_schema/versions/2015-01-01/preview'
        res = app.post(url, status='*')
        assert 401 == res.status_code

    # tests for version edit

    @pytest.mark.parametrize('group', ALLOWED_NO_EDITOR)
    def test_forms_versions_edit(self, app, db_session, group):
        url = '/forms/test_schema/versions/2015-01-01'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        data = {
            '__url__': url,
            'name': 'test_schema',
            'title': 'test_title',
            'fields': [],
            'hasFields': False,
            'isNew': False,
            'publish_date': '2015-01-01'
        }

        res = app.put_json(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', NOT_ALLOWED_W_EDITOR)
    def test_not_allowed_forms_versions_edit(self, app, db_session, group):
        url = '/forms/test_schema/versions/2015-01-01'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        data = {
            '__url__': url,
            'name': 'test_schema',
            'title': 'test_title',
            'fields': [],
            'hasFields': False,
            'isNew': False,
            'publish_date': '2015-01-01'
        }

        res = app.put_json(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated_versions_edit(self, app, db_session):
        url = '/forms/test_schema/versions/2015-01-01'
        res = app.put_json(url, status='*')
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_ALLOWED)
    def test_forms_versions_edit_unpublished(self, app, db_session, group):
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        data = {
            '__url__': url,
            'name': 'test_schema',
            'title': 'test_title',
            'fields': [],
            'hasFields': False,
            'isNew': False,
            'publish_date': '2015-01-01'
        }

        res = app.put_json(
            url.format(form_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_NOT_ALLOWED)
    def test_not_allowed_forms_versions_edit_unpublished(
            self, app, db_session, group):
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        data = {
            '__url__': url,
            'name': 'test_schema',
            'title': 'test_title',
            'fields': [],
            'hasFields': False,
            'isNew': False,
            'publish_date': '2015-01-01'
        }

        res = app.put_json(
            url.format(form_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated_versions_edit_unpublished(
            self, app, db_session):
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}'

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        res = app.put_json(url.format(form_id), status='*')
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', ALLOWED_NO_EDITOR)
    def test_forms_versions_edit_publish(self, app, db_session, group):
        url = '/forms/test_schema/versions/2015-01-01?publish'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        data = {
            '__url__': url,
            'name': 'test_schema',
            'title': 'test_title',
            'fields': [],
            'hasFields': False,
            'isNew': False,
            'publish_date': '2015-01-01'
        }

        res = app.put_json(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', NOT_ALLOWED_W_EDITOR)
    def test_not_allowed_forms_versions_edit_publish(
            self, app, db_session, group):
        url = '/forms/test_schema/versions/2015-01-01?publish'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        data = {
            '__url__': url,
            'name': 'test_schema',
            'title': 'test_title',
            'fields': [],
            'hasFields': False,
            'isNew': False,
            'publish_date': '2015-01-01'
        }

        res = app.put_json(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated_versions_edit_publish(self, app, db_session):
        url = '/forms/test_schema/versions/2015-01-01?publish'
        res = app.put_json(url, status='*')
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_ALLOWED)
    def test_forms_versions_post_draft(self, app, db_session, group):
        url = '/forms/test_schema/versions/2015-01-01?draft'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        data = {
            '__url__': url,
            'name': 'test_schema',
            'title': 'test_title',
            'fields': [],
            'hasFields': False,
            'isNew': False,
            'publish_date': '2015-01-01'
        }

        res = app.post(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True,
            params=data)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_NOT_ALLOWED)
    def test_not_allowed_forms_versions_post_draft(
            self, app, db_session, group):
        url = '/forms/test_schema/versions/2015-01-01?draft'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        data = {
            '__url__': url,
            'name': 'test_schema',
            'title': 'test_title',
            'fields': [],
            'hasFields': False,
            'isNew': False,
            'publish_date': '2015-01-01'
        }

        res = app.post(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True,
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated_versions_post_draft(self, app, db_session):
        url = '/forms/test_schema/versions/2015-01-01?draft'
        res = app.post(url, status='*')
        assert 401 == res.status_code

    # test forms version editor

    @pytest.mark.parametrize('group', ALLOWED_NO_EDITOR)
    def test_forms_versions_editor(self, app, db_session, group):
        url = '/forms/test_schema/versions/2015-01-01/editor'

        environ = make_environ(userid=USERID, groups=[group])
        res = app.get(url, extra_environ=environ, status='*')
        assert 200 == res.status_code

    @pytest.mark.parametrize('group', NOT_ALLOWED_W_EDITOR)
    def test_not_allowed_forms_versions_editor(self, app, db_session, group):
        url = '/forms/test_schema/versions/2015-01-01/editor'

        environ = make_environ(userid=USERID, groups=[group])
        res = app.delete(url, extra_environ=environ, status='*')
        assert 403 == res.status_code

    def test_not_authenticated_versions_editor(self, app, db_session):
        url = '/forms/test_schema/versions/2015-01-01/editor'
        res = app.get(url, status='*')
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_ALLOWED)
    def test_forms_versions_editor_unpublished(self, app, db_session, group):
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/editor'

        environ = make_environ(userid=USERID, groups=[group])

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        res = app.get(
            url.format(form_id), extra_environ=environ, status='*')

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_NOT_ALLOWED)
    def test_not_allowed_forms_versions_editor_unpublished(
            self, app, db_session, group):
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/editor'

        environ = make_environ(userid=USERID, groups=[group])

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        res = app.get(
            url.format(form_id), extra_environ=environ, status='*')

        assert 403 == res.status_code

    def test_not_authenticated_versions_editor_unpublished(
            self, app, db_session):
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/editor'

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        res = app.get(url.format(form_id), status='*')
        assert 401 == res.status_code

    # test forms version delete

    @pytest.mark.parametrize('group', ALLOWED_NO_EDITOR)
    def test_forms_versions_delete(self, app, db_session, group):
        url = '/forms/test_schema/versions/2015-01-01'
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)
        res = app.delete(
            url,
            extra_environ=environ,
            xhr=True,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            }
        )

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', NOT_ALLOWED_W_EDITOR)
    def test_not_allowed_forms_versions_delete(self, app, db_session, group):
        url = '/forms/test_schema/versions/2015-01-01'
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)
        res = app.delete(
            url,
            extra_environ=environ,
            xhr=True,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            }
        )

        assert 403 == res.status_code

    def test_not_authenticated_versions_delete(self, app, db_session):
        url = '/forms/test_schema/versions/2015-01-01'
        res = app.delete(url, status='*')
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_ALLOWED)
    def test_forms_versions_delete_unpublished(self, app, db_session, group):
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}'
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        res = app.delete(
            url.format(form_id),
            extra_environ=environ,
            xhr=True,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            }
        )

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_NOT_ALLOWED)
    def test_not_allowed_forms_versions_delete_unpublished(
            self, app, db_session, group):
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}'
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        res = app.delete(
            url.format(form_id),
            extra_environ=environ,
            xhr=True,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            }
        )

        assert 403 == res.status_code

    def test_not_authenticated_versions_unpublished_delete(
            self, app, db_session):
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}'

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        res = app.delete(url.format(form_id), status='*')
        assert 401 == res.status_code

    # tests for fields

    @pytest.mark.parametrize('group', ALL_ALLOWED)
    def test_view_field_json(self, app, db_session, group):
        url = '/forms/test_schema/versions/2015-01-01/fields/test_field'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        res = app.get(
            url,
            status='*',
            xhr=True,
            extra_environ=environ,
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            })
        assert 200 == res.status_code

    def test_not_authenticated_view_field_json(self, app, db_session):
        url = '/forms/test_schema/versions/2015-01-01/fields/test_field'

        res = app.delete(url, status='*', xhr=True)
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', ALLOWED_NO_EDITOR)
    def test_move_field(self, app, db_session, group):
        url = '/forms/test_schema/versions/2015-01-01/fields/text_box2?move'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        data = {
            'index': 0
        }

        res = app.put_json(
            url,
            status='*',
            extra_environ=environ,
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', NOT_ALLOWED_W_EDITOR)
    def test_not_allowed_move_field(self, app, db_session, group):
        url = '/forms/test_schema/versions/2015-01-01/fields/text_box2?move'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        data = {
            'index': 0
        }

        res = app.put_json(
            url,
            status='*',
            extra_environ=environ,
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated_move_field(self, app, db_session):
        url = '/forms/test_schema/versions/2015-01-01/fields/text_box2?move'

        res = app.put(url, status='*', xhr=True)
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_ALLOWED)
    def test_move_field_unpublished(self, app, db_session, group):
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/fields/text_box2?move'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        data = {
            'index': 0
        }

        res = app.put_json(
            url.format(form_id),
            status='*',
            extra_environ=environ,
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_NOT_ALLOWED)
    def test_not_allowed_move_field_unpublished(self, app, db_session, group):
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/fields/text_box2?move'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        data = {
            'index': 0
        }

        res = app.put_json(
            url.format(form_id),
            status='*',
            extra_environ=environ,
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated_move_field_unpublished(self, app, db_session):
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/fields/text_box2?move'

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        res = app.put(url.format(form_id), status='*', xhr=True)
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_ALLOWED)
    def test_add_field(self, app, db_session, group):
        url = '/forms/test_schema/versions/2015-01-01/fields'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        data = {
            'choiceInputType': 'radio',
            'choices': [],
            'name': 'test_field_add',
            'title': 'test_title_add',
            'description': 'test_desc_add',
            'type': 'string',
            'is_required': False,
            'isNew': True,
            'isSection': False,
            'fields': [],
            'isLimitAllowed': True,
            'hasFields': False,
            'index': 0
        }

        res = app.post_json(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data
        )

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_NOT_ALLOWED)
    def test_not_allowed_add_field(self, app, db_session, group):
        url = '/forms/test_schema/versions/2015-01-01/fields'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        data = {
            'choiceInputType': 'radio',
            'choices': [],
            'name': 'test_field',
            'title': 'test_title',
            'description': 'test_desc',
            'type': 'string',
            'is_required': False,
            'isNew': True,
            'isSection': False,
            'fields': [],
            'isLimitAllowed': True,
            'hasFields': False,
            'index': 0

        }

        res = app.post_json(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data
        )

        assert 403 == res.status_code

    def test_not_authenticated_add_field(self, app, db_session):
        url = '/forms/test_schema/versions/2015-01-01/fields'
        res = app.post(url, status='*', xhr=True)
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', ALLOWED_NO_EDITOR)
    def test_edit_field(self, app, db_session, group):
        url = '/forms/test_schema/versions/2015-01-01/fields/test_field'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        data = {
            'name': 'test_field_add',
            'type': 'string',
            'title': 'updated title'
        }

        res = app.put_json(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data
        )

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', NOT_ALLOWED_W_EDITOR)
    def test_not_allowed_edit_field(self, app, db_session, group):
        url = '/forms/test_schema/versions/2015-01-01/fields/test_field'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        data = {
            'name': 'test_field_add',
            'type': 'string',
            'title': 'updated title'
        }

        res = app.put_json(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data
        )

        assert 403 == res.status_code

    def test_not_authenticated_edit_field(self, app, db_session):
        url = '/forms/test_schema/versions/2015-01-01/fields/test_field'
        res = app.put(url, status='*', xhr=True)
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_ALLOWED)
    def test_edit_field_unpublished(self, app, db_session, group):
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/fields/test_field2'

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        data = {
            'name': 'test_field_add',
            'type': 'string',
            'title': 'updated title'
        }

        res = app.put_json(
            url.format(form_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data
        )

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_NOT_ALLOWED)
    def test_not_allowed_edit_field_unpublished(self, app, db_session, group):
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/fields/test_field2'

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        data = {
            'name': 'test_field_add',
            'type': 'string',
            'title': 'updated title'
        }

        res = app.put_json(
            url.format(form_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data
        )

        assert 403 == res.status_code

    def test_not_authenticated_edit_field_unpublised(self, app, db_session):
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/fields/test_field2'

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        res = app.put(url.format(form_id), status='*', xhr=True)
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', ALLOWED_NO_EDITOR)
    def test_edit_validate_fields(self, app, db_session, group):
        url = '/forms/test_schema/versions/2015-01-01/fields?validate'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        data = {
            'choiceInputType': 'radio',
            'choices': [],
            'name': 'test_field',
            'title': 'test_title',
            'description': 'test_desc',
            'type': 'string',
            'is_required': False,
            'isNew': True,
            'isSection': False,
            'fields': [],
            'isLimitAllowed': True,
            'hasFields': False,
            'index': 0
        }

        res = app.put_json(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data
        )

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', NOT_ALLOWED_W_EDITOR)
    def test_not_allowed_edit_validate_fields(self, app, db_session, group):
        url = '/forms/test_schema/versions/2015-01-01/fields?validate'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        data = {
            'choiceInputType': 'radio',
            'choices': [],
            'name': 'test_field',
            'title': 'test_title',
            'description': 'test_desc',
            'type': 'string',
            'is_required': False,
            'isNew': True,
            'isSection': False,
            'fields': [],
            'isLimitAllowed': True,
            'hasFields': False,
            'index': 0
        }

        res = app.put_json(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data
        )

        assert 403 == res.status_code

    def test_not_authenticated_edit_validate_fields(self, app, db_session):
        url = '/forms/test_schema/versions/2015-01-01/fields?validate'

        res = app.put(url, status='*', xhr=True)
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_ALLOWED)
    def test_edit_validate_fields_unpublished(self, app, db_session, group):
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/fields?validate'

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        data = {
            'choiceInputType': 'radio',
            'choices': [],
            'name': 'test_field',
            'title': 'test_title',
            'description': 'test_desc',
            'type': 'string',
            'is_required': False,
            'isNew': True,
            'isSection': False,
            'fields': [],
            'isLimitAllowed': True,
            'hasFields': False,
            'index': 0
        }

        res = app.put_json(
            url.format(form_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data
        )

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_NOT_ALLOWED)
    def test_not_allowed_edit_validate_fields_unpublished(
            self, app, db_session, group):
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/fields?validate'

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        data = {
            'choiceInputType': 'radio',
            'choices': [],
            'name': 'test_field',
            'title': 'test_title',
            'description': 'test_desc',
            'type': 'string',
            'is_required': False,
            'isNew': True,
            'isSection': False,
            'fields': [],
            'isLimitAllowed': True,
            'hasFields': False,
            'index': 0
        }

        res = app.put_json(
            url.format(form_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data
        )

        assert 403 == res.status_code

    def test_not_authenticated_edit_validate_fields_unpublished(
            self, app, db_session):
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/fields?validate'

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        res = app.put(url.format(form_id), status='*', xhr=True)
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', ALLOWED_NO_EDITOR)
    def test_edit_validate_field(self, app, db_session, group):
        url = '/forms/test_schema/versions/2015-01-01/fields/' \
              'test_field?validate'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        res = app.get(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            }
        )

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', NOT_ALLOWED_W_EDITOR)
    def test_not_allowed_edit_validate_field(self, app, db_session, group):
        url = '/forms/test_schema/versions/2015-01-01/fields/' \
              'test_field?validate'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        res = app.get(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            }
        )

        assert 403 == res.status_code

    def test_not_authenticated_edit_validate_field(self, app, db_session):
        url = '/forms/test_schema/versions/2015-01-01/fields/' \
              'test_field?validate'

        environ = make_environ(userid=USERID)
        csrf_token = get_csrf_token(app, environ)

        res = app.get(
            url,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            }
        )

        assert 401 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_ALLOWED)
    def test_edit_validate_field_unpublished(self, app, db_session, group):
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/fields/' \
              'test_field2?validate'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        res = app.get(
            url.format(form_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            }
        )

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_NOT_ALLOWED)
    def test_not_allowed_edit_validate_field_unpublished(
            self, app, db_session, group):
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/fields/' \
              'test_field2?validate'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        res = app.get(
            url.format(form_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            }
        )

        assert 403 == res.status_code

    def test_not_authenticated_edit_validate_field_unpublished(
            self, app, db_session):
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/fields/' \
              'test_field2?validate'

        environ = make_environ(userid=USERID)
        csrf_token = get_csrf_token(app, environ)

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        res = app.get(
            url.format(form_id),
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            }
        )

        assert 401 == res.status_code

    @pytest.mark.parametrize('group', ALLOWED_NO_EDITOR)
    def test_delete_field(self, app, db_session, group):
        url = '/forms/test_schema/versions/2015-01-01/fields/test_field'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        res = app.delete(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True
        )

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', NOT_ALLOWED_W_EDITOR)
    def test_not_allowed_delete_field(self, app, db_session, group):
        url = '/forms/test_schema/versions/2015-01-01/fields/test_field'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        res = app.delete(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True
        )

        assert 403 == res.status_code

    def test_not_authenticated_delete_field(self, app, db_session):
        url = '/forms/test_schema/versions/2015-01-01/fields/test_field'

        res = app.delete(url, status='*', xhr=True)
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_ALLOWED)
    def test_delete_field_unpublished(self, app, db_session, group):
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/fields/test_field2'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        res = app.delete(
            url.format(form_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True
        )

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_NOT_ALLOWED)
    def test_not_allowed_delete_field_unpublished(
            self, app, db_session, group):
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/fields/test_field2'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        res = app.delete(
            url.format(form_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True
        )

        assert 403 == res.status_code

    def test_not_authenticated_delete_field_unpublished(self, app, db_session):
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/fields/test_field2'

        form_id = db_session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        res = app.delete(url.format(form_id), status='*', xhr=True)

        assert 401 == res.status_code
