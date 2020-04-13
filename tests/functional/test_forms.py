import pytest

from tests.testing import USERID, make_environ, get_csrf_token


class TestPermissionForms:
    ALL_ALLOWED = ('administrator', 'manager', 'editor', None)
    DEFAULT_ALLOWED = ('administrator', 'manager', 'editor')
    DEFAULT_NOT_ALLOWED = ('enterer', 'reviewer', 'member')
    ALLOWED_NO_EDITOR = ('administrator', 'manager')
    NOT_ALLOWED_W_EDITOR = ('editor', 'enterer', 'reviewer', 'member')

    @pytest.fixture(autouse=True)
    def populate(self, app, using_dbsession):
        from datetime import date
        from occams import models

        with using_dbsession(app) as dbsession:
            form_published = models.Schema(
                name='test_schema',
                title='test_title',
                publish_date=date(2015, 1, 1)
            )

            form_unpublished = models.Schema(
                name='test_schema2',
                title='test_title2',
            )

            dbsession.add(models.Attribute(
                name='test_field',
                title='test_title',
                description='test_desc',
                type='string',
                schema=form_published,
                order=0
            ))

            dbsession.add(models.Attribute(
                name='text_box2',
                title='text_box2',
                description='text_box_desc2',
                type='string',
                schema=form_published,
                order=1
            ))

            dbsession.add(models.Attribute(
                name='test_field2',
                title='test_title2',
                description='test_desc2',
                type='string',
                schema=form_unpublished,
                order=0
            ))

            dbsession.add(models.Attribute(
                name='text_box2',
                title='text_box2',
                description='text_box_desc2',
                type='string',
                schema=form_unpublished,
                order=1
            ))

            dbsession.flush()
            self.form_published_id = form_published.id
            self.form_unpublished_id = form_unpublished.id

    # tests for forms

    @pytest.mark.parametrize('group', ALL_ALLOWED)
    def test_forms_view(self, testapp, group):
        url = '/forms'

        environ = make_environ(userid=USERID, groups=[group])
        res = testapp.get(url, extra_environ=environ)
        assert 200 == res.status_code

    def test_not_authenticated_forms(self, testapp):
        url = '/forms'
        res = testapp.get(url, status='*')
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', ALL_ALLOWED)
    def test_forms_view_xhr(self, testapp, group):
        url = '/forms'

        environ = make_environ(userid=USERID, groups=[group])
        res = testapp.get(url, extra_environ=environ, xhr=True)
        assert 200 == res.status_code

    def test_not_authenticated_forms_xhr(self, testapp):
        url = '/forms'
        res = testapp.get(url, status='*', xhr=True)
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_ALLOWED)
    def test_forms_upload_json(self, testapp, group):
        import json

        url = '/forms?files'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        data = {
            'title': 'OMG',
            'storage': 'eav',
            'publish_date': '2015-05-26',
            "name": 'omg'
        }

        res = testapp.post(
            url,
            extra_environ=environ,
            status='*',
            upload_files=[('files', 'upload.json', json.dumps(data).encode())],
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_NOT_ALLOWED)
    def test_not_allowed_forms_upload_json(self, testapp, group):
        import json

        url = '/forms?files'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        data = {
            'title': 'OMG',
            'storage': 'eav',
            'publish_date': '2015-05-26',
            "name": 'omg'
        }

        res = testapp.post(
            url,
            extra_environ=environ,
            status='*',
            upload_files=[('files', 'upload.json', json.dumps(data).encode())],
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True)

        assert 403 == res.status_code

    def test_not_authenticated_files_upload(self, testapp):
        url = '/forms?files'
        res = testapp.post(url, status='*', xhr=True)
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_ALLOWED)
    def test_forms_add_json_validate(self, testapp, group):
        url = '/forms?validate'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        data = {
            'name': 'test_form',
            'title': 'test_form',
            'versions': [],
            'isNew': True,
            'hasVersions': False
        }

        res = testapp.get(
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
    def test_not_allowed_forms_add_json_validate(self, testapp, group):
        url = '/forms?validate'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        data = {
            'name': 'test_form',
            'title': 'test_form',
            'versions': [],
            'isNew': True,
            'hasVersions': False
        }

        res = testapp.get(
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

    def test_not_authenticated_validate_field(self, testapp):
        url = '/forms?validate'

        res = testapp.get(url, status='*', xhr=True)
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_ALLOWED)
    def test_forms_add(self, testapp, group):
        url = '/forms'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        data = {
            'name': 'test_form',
            'title': 'test_form',
            'versions': [],
            'isNew': True,
            'hasVersions': False
        }

        res = testapp.post_json(
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
    def test_not_allowed_forms_add(self, testapp, group):
        url = '/forms'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        data = {
            'name': 'test_form',
            'title': 'test_form',
            'versions': [],
            'isNew': True,
            'hasVersions': False
        }

        res = testapp.post_json(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated_forms_add(self, testapp):
        url = '/forms'
        res = testapp.post_json(url, status='*')
        assert 401 == res.status_code

    # test for versions

    @pytest.mark.parametrize('group', ALL_ALLOWED)
    def test_forms_versions(self, testapp, group):
        url = '/forms/test_schema/versions/2015-01-01'

        environ = make_environ(userid=USERID, groups=[group])
        res = testapp.get(url, extra_environ=environ)
        assert 200 == res.status_code

    def test_not_authenticated_versions(self, testapp):
        url = '/forms/test_schema/versions/2015-01-01'
        res = testapp.get(url, status='*')
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', ALL_ALLOWED)
    def test_forms_versions_xhr(self, testapp, group):
        # test same url with xhr
        url = '/forms/test_schema/versions/2015-01-01'

        environ = make_environ(userid=USERID, groups=[group])
        res = testapp.get(url, extra_environ=environ, xhr=True)
        assert 200 == res.status_code

    def test_not_authenticated_versions_xhr(self, testapp):
        url = '/forms/test_schema/versions/2015-01-01'
        res = testapp.get(url, status='*', xhr=True)
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', ALL_ALLOWED)
    def test_forms_versions_download_json(self, testapp, group):
        url = '/forms/test_schema/versions/2015-01-01?download=json'

        environ = make_environ(userid=USERID, groups=[group])
        res = testapp.get(url, extra_environ=environ)
        assert 200 == res.status_code

    def test_not_authenticated_versions_download_json(self, testapp):
        url = '/forms/test_schema/versions/2015-01-01?download=json'
        res = testapp.get(url, status='*')
        assert 401 == res.status_code

    # tests for versions preview

    @pytest.mark.parametrize('group', ALL_ALLOWED)
    def test_forms_versions_preview(self, testapp, group):
        url = '/forms/test_schema/versions/2015-01-01/preview'

        environ = make_environ(userid=USERID, groups=[group])
        res = testapp.get(url, extra_environ=environ)
        assert 200 == res.status_code

    def test_not_authenticated_preview(self, testapp):
        url = '/forms/test_schema/versions/2015-01-01/preview'
        res = testapp.get(url, status='*')
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', ALL_ALLOWED)
    def test_forms_versions_preview_post(self, testapp, group):
        url = '/forms/test_schema/versions/2015-01-01/preview'

        data = {}

        environ = make_environ(userid=USERID, groups=[group])
        res = testapp.post(
            url,
            extra_environ=environ,
            status='*',
            params=data)

        assert 200 == res.status_code

    def test_not_authenticated_preview_post(self, testapp):
        url = '/forms/test_schema/versions/2015-01-01/preview'
        res = testapp.post(url, status='*')
        assert 401 == res.status_code

    # tests for version edit

    @pytest.mark.parametrize('group', ALLOWED_NO_EDITOR)
    def test_forms_versions_edit(self, testapp, group):
        url = '/forms/test_schema/versions/2015-01-01'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        data = {
            '__url__': url,
            'name': 'test_schema',
            'title': 'test_title',
            'fields': [],
            'hasFields': False,
            'isNew': False,
            'publish_date': '2015-01-01'
        }

        res = testapp.put_json(
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
    def test_not_allowed_forms_versions_edit(self, testapp, group):
        url = '/forms/test_schema/versions/2015-01-01'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        data = {
            '__url__': url,
            'name': 'test_schema',
            'title': 'test_title',
            'fields': [],
            'hasFields': False,
            'isNew': False,
            'publish_date': '2015-01-01'
        }

        res = testapp.put_json(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated_versions_edit(self, testapp):
        url = '/forms/test_schema/versions/2015-01-01'
        res = testapp.put_json(url, status='*')
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_ALLOWED)
    def test_forms_versions_edit_unpublished(self, testapp, group):
        url = '/forms/test_schema2/versions/{}'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        form_id = self.form_unpublished_id

        data = {
            '__url__': url,
            'name': 'test_schema',
            'title': 'test_title',
            'fields': [],
            'hasFields': False,
            'isNew': False,
            'publish_date': '2015-01-01'
        }

        res = testapp.put_json(
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
            self, testapp, group):
        url = '/forms/test_schema2/versions/{}'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        form_id = self.form_unpublished_id

        data = {
            '__url__': url,
            'name': 'test_schema',
            'title': 'test_title',
            'fields': [],
            'hasFields': False,
            'isNew': False,
            'publish_date': '2015-01-01'
        }

        res = testapp.put_json(
            url.format(form_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated_versions_edit_unpublished(self, testapp):
        url = '/forms/test_schema2/versions/{}'

        form_id = self.form_unpublished_id

        res = testapp.put_json(url.format(form_id), status='*')
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', ALLOWED_NO_EDITOR)
    def test_forms_versions_edit_publish(self, testapp, group):
        url = '/forms/test_schema/versions/2015-01-01?publish'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        data = {
            '__url__': url,
            'name': 'test_schema',
            'title': 'test_title',
            'fields': [],
            'hasFields': False,
            'isNew': False,
            'publish_date': '2015-01-01'
        }

        res = testapp.put_json(
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
            self, testapp, group):
        url = '/forms/test_schema/versions/2015-01-01?publish'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        data = {
            '__url__': url,
            'name': 'test_schema',
            'title': 'test_title',
            'fields': [],
            'hasFields': False,
            'isNew': False,
            'publish_date': '2015-01-01'
        }

        res = testapp.put_json(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated_versions_edit_publish(self, testapp):
        url = '/forms/test_schema/versions/2015-01-01?publish'
        res = testapp.put_json(url, status='*')
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_ALLOWED)
    def test_forms_versions_post_draft(self, testapp, group):
        url = '/forms/test_schema/versions/2015-01-01?draft'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        data = {
            '__url__': url,
            'name': 'test_schema',
            'title': 'test_title',
            'fields': [],
            'hasFields': False,
            'isNew': False,
            'publish_date': '2015-01-01'
        }

        res = testapp.post(
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
            self, testapp, group):
        url = '/forms/test_schema/versions/2015-01-01?draft'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        data = {
            '__url__': url,
            'name': 'test_schema',
            'title': 'test_title',
            'fields': [],
            'hasFields': False,
            'isNew': False,
            'publish_date': '2015-01-01'
        }

        res = testapp.post(
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

    def test_not_authenticated_versions_post_draft(self, testapp):
        url = '/forms/test_schema/versions/2015-01-01?draft'
        res = testapp.post(url, status='*')
        assert 401 == res.status_code

    # test forms version editor

    @pytest.mark.parametrize('group', ALLOWED_NO_EDITOR)
    def test_forms_versions_editor(self, testapp, group):
        url = '/forms/test_schema/versions/2015-01-01/editor'

        environ = make_environ(userid=USERID, groups=[group])
        res = testapp.get(url, extra_environ=environ, status='*')
        assert 200 == res.status_code

    @pytest.mark.parametrize('group', NOT_ALLOWED_W_EDITOR)
    def test_not_allowed_forms_versions_editor(self, testapp, group):
        url = '/forms/test_schema/versions/2015-01-01/editor'

        environ = make_environ(userid=USERID, groups=[group])
        res = testapp.delete(url, extra_environ=environ, status='*')
        assert 403 == res.status_code

    def test_not_authenticated_versions_editor(self, testapp):
        url = '/forms/test_schema/versions/2015-01-01/editor'
        res = testapp.get(url, status='*')
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_ALLOWED)
    def test_forms_versions_editor_unpublished(self, testapp, group):
        url = '/forms/test_schema2/versions/{}/editor'

        environ = make_environ(userid=USERID, groups=[group])

        form_id = self.form_unpublished_id

        res = testapp.get(
            url.format(form_id), extra_environ=environ, status='*')

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_NOT_ALLOWED)
    def test_not_allowed_forms_versions_editor_unpublished(self, testapp, group):

        url = '/forms/test_schema2/versions/{}/editor'

        environ = make_environ(userid=USERID, groups=[group])

        form_id = self.form_unpublished_id

        res = testapp.get(
            url.format(form_id), extra_environ=environ, status='*')

        assert 403 == res.status_code

    def test_not_authenticated_versions_editor_unpublished(
            self, testapp):

        url = '/forms/test_schema2/versions/{}/editor'

        form_id = self.form_unpublished_id

        res = testapp.get(url.format(form_id), status='*')
        assert 401 == res.status_code

    # test forms version delete

    @pytest.mark.parametrize('group', ALLOWED_NO_EDITOR)
    def test_forms_versions_delete(self, testapp, group):
        url = '/forms/test_schema/versions/2015-01-01'
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)
        res = testapp.delete(
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
    def test_not_allowed_forms_versions_delete(self, testapp, group):
        url = '/forms/test_schema/versions/2015-01-01'
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)
        res = testapp.delete(
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

    def test_not_authenticated_versions_delete(self, testapp):
        url = '/forms/test_schema/versions/2015-01-01'
        res = testapp.delete(url, status='*')
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_ALLOWED)
    def test_forms_versions_delete_unpublished(self, testapp, group):
        url = '/forms/test_schema2/versions/{}'
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        form_id = self.form_unpublished_id

        res = testapp.delete(
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
            self, testapp, group):

        url = '/forms/test_schema2/versions/{}'
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        form_id = self.form_unpublished_id

        res = testapp.delete(
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
            self, testapp):

        url = '/forms/test_schema2/versions/{}'

        form_id = self.form_unpublished_id

        res = testapp.delete(url.format(form_id), status='*')
        assert 401 == res.status_code

    # tests for fields

    @pytest.mark.parametrize('group', ALL_ALLOWED)
    def test_view_field_json(self, testapp, group):
        url = '/forms/test_schema/versions/2015-01-01/fields/test_field'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        res = testapp.get(
            url,
            status='*',
            xhr=True,
            extra_environ=environ,
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            })
        assert 200 == res.status_code

    def test_not_authenticated_view_field_json(self, testapp):
        url = '/forms/test_schema/versions/2015-01-01/fields/test_field'

        res = testapp.delete(url, status='*', xhr=True)
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', ALLOWED_NO_EDITOR)
    def test_move_field(self, testapp, group):
        url = '/forms/test_schema/versions/2015-01-01/fields/text_box2?move'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        data = {
            'index': 0
        }

        res = testapp.put_json(
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
    def test_not_allowed_move_field(self, testapp, group):
        url = '/forms/test_schema/versions/2015-01-01/fields/text_box2?move'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        data = {
            'index': 0
        }

        res = testapp.put_json(
            url,
            status='*',
            extra_environ=environ,
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated_move_field(self, testapp):
        url = '/forms/test_schema/versions/2015-01-01/fields/text_box2?move'

        res = testapp.put(url, status='*', xhr=True)
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_ALLOWED)
    def test_move_field_unpublished(self, testapp, group):
        url = '/forms/test_schema2/versions/{}/fields/text_box2?move'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        form_id = self.form_unpublished_id

        data = {
            'index': 0
        }

        res = testapp.put_json(
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
    def test_not_allowed_move_field_unpublished(self, testapp, group):
        url = '/forms/test_schema2/versions/{}/fields/text_box2?move'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        form_id = self.form_unpublished_id

        data = {
            'index': 0
        }

        res = testapp.put_json(
            url.format(form_id),
            status='*',
            extra_environ=environ,
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated_move_field_unpublished(self, testapp):
        url = '/forms/test_schema2/versions/{}/fields/text_box2?move'

        form_id = self.form_unpublished_id

        res = testapp.put(url.format(form_id), status='*', xhr=True)
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_ALLOWED)
    def test_add_field(self, testapp, group):
        url = '/forms/test_schema/versions/2015-01-01/fields'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

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

        res = testapp.post_json(
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
    def test_not_allowed_add_field(self, testapp, group):
        url = '/forms/test_schema/versions/2015-01-01/fields'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

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

        res = testapp.post_json(
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

    def test_not_authenticated_add_field(self, testapp):
        url = '/forms/test_schema/versions/2015-01-01/fields'
        res = testapp.post(url, status='*', xhr=True)
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', ALLOWED_NO_EDITOR)
    def test_edit_field(self, testapp, group):
        url = '/forms/test_schema/versions/2015-01-01/fields/test_field'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        data = {
            'name': 'test_field_add',
            'type': 'string',
            'title': 'updated title'
        }

        res = testapp.put_json(
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
    def test_not_allowed_edit_field(self, testapp, group):
        url = '/forms/test_schema/versions/2015-01-01/fields/test_field'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        data = {
            'name': 'test_field_add',
            'type': 'string',
            'title': 'updated title'
        }

        res = testapp.put_json(
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

    def test_not_authenticated_edit_field(self, testapp):
        url = '/forms/test_schema/versions/2015-01-01/fields/test_field'
        res = testapp.put(url, status='*', xhr=True)
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_ALLOWED)
    def test_edit_field_unpublished(self, testapp, group):
        url = '/forms/test_schema2/versions/{}/fields/test_field2'

        form_id = self.form_unpublished_id

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        data = {
            'name': 'test_field_add',
            'type': 'string',
            'title': 'updated title'
        }

        res = testapp.put_json(
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
    def test_not_allowed_edit_field_unpublished(self, testapp, group):
        url = '/forms/test_schema2/versions/{}/fields/test_field2'

        form_id = self.form_unpublished_id

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        data = {
            'name': 'test_field_add',
            'type': 'string',
            'title': 'updated title'
        }

        res = testapp.put_json(
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

    def test_not_authenticated_edit_field_unpublised(self, testapp):
        url = '/forms/test_schema2/versions/{}/fields/test_field2'

        form_id = self.form_unpublished_id

        res = testapp.put(url.format(form_id), status='*', xhr=True)
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', ALLOWED_NO_EDITOR)
    def test_edit_validate_fields(self, testapp, group):
        url = '/forms/test_schema/versions/2015-01-01/fields?validate'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

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

        res = testapp.put_json(
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
    def test_not_allowed_edit_validate_fields(self, testapp, group):
        url = '/forms/test_schema/versions/2015-01-01/fields?validate'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

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

        res = testapp.put_json(
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

    def test_not_authenticated_edit_validate_fields(self, testapp):
        url = '/forms/test_schema/versions/2015-01-01/fields?validate'

        res = testapp.put(url, status='*', xhr=True)
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_ALLOWED)
    def test_edit_validate_fields_unpublished(self, testapp, group):
        url = '/forms/test_schema2/versions/{}/fields?validate'

        form_id = self.form_unpublished_id

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

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

        res = testapp.put_json(
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
            self, testapp, group):
        url = '/forms/test_schema2/versions/{}/fields?validate'

        form_id = self.form_unpublished_id

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

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

        res = testapp.put_json(
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
            self, testapp):
        url = '/forms/test_schema2/versions/{}/fields?validate'

        form_id = self.form_unpublished_id

        res = testapp.put(url.format(form_id), status='*', xhr=True)
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', ALLOWED_NO_EDITOR)
    def test_edit_validate_field(self, testapp, group):
        url = '/forms/test_schema/versions/2015-01-01/fields/' \
              'test_field?validate'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        res = testapp.get(
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
    def test_not_allowed_edit_validate_field(self, testapp, group):
        url = '/forms/test_schema/versions/2015-01-01/fields/' \
              'test_field?validate'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        res = testapp.get(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            }
        )

        assert 403 == res.status_code

    def test_not_authenticated_edit_validate_field(self, testapp):
        url = '/forms/test_schema/versions/2015-01-01/fields/' \
              'test_field?validate'

        environ = make_environ(userid=USERID)
        csrf_token = get_csrf_token(testapp, environ)

        res = testapp.get(
            url,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            }
        )

        assert 401 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_ALLOWED)
    def test_edit_validate_field_unpublished(self, testapp, group):
        url = '/forms/test_schema2/versions/{}/fields/' \
              'test_field2?validate'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        form_id = self.form_unpublished_id

        res = testapp.get(
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
            self, testapp, group):
        url = '/forms/test_schema2/versions/{}/fields/' \
              'test_field2?validate'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        form_id = self.form_unpublished_id

        res = testapp.get(
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
            self, testapp):
        url = '/forms/test_schema2/versions/{}/fields/' \
              'test_field2?validate'

        environ = make_environ(userid=USERID)
        csrf_token = get_csrf_token(testapp, environ)

        form_id = self.form_unpublished_id

        res = testapp.get(
            url.format(form_id),
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            }
        )

        assert 401 == res.status_code

    @pytest.mark.parametrize('group', ALLOWED_NO_EDITOR)
    def test_delete_field(self, testapp, group):
        url = '/forms/test_schema/versions/2015-01-01/fields/test_field'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        res = testapp.delete(
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
    def test_not_allowed_delete_field(self, testapp, group):
        url = '/forms/test_schema/versions/2015-01-01/fields/test_field'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        res = testapp.delete(
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

    def test_not_authenticated_delete_field(self, testapp):
        url = '/forms/test_schema/versions/2015-01-01/fields/test_field'

        res = testapp.delete(url, status='*', xhr=True)
        assert 401 == res.status_code

    @pytest.mark.parametrize('group', DEFAULT_ALLOWED)
    def test_delete_field_unpublished(self, testapp, group):
        url = '/forms/test_schema2/versions/{}/fields/test_field2'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        form_id = self.form_unpublished_id

        res = testapp.delete(
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
            self, testapp, group):
        url = '/forms/test_schema2/versions/{}/fields/test_field2'

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        form_id = self.form_unpublished_id

        res = testapp.delete(
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

    def test_not_authenticated_delete_field_unpublished(self, testapp):
        url = '/forms/test_schema2/versions/{}/fields/test_field2'

        form_id = self.form_unpublished_id

        res = testapp.delete(url.format(form_id), status='*', xhr=True)

        assert 401 == res.status_code
