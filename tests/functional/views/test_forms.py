from ddt import ddt, data
from tests import FunctionalFixture, USERID


@ddt
class TestPermissionForms(FunctionalFixture):
    ALL_ALLOWED = ('administrator', 'manager', 'editor', None)
    DEFAULT_ALLOWED = ('administrator', 'manager', 'editor')
    DEFAULT_NOT_ALLOWED = ('enterer', 'reviewer', 'member')
    ALLOWED_NO_EDITOR = ('administrator', 'manager')
    NOT_ALLOWED_W_EDITOR = ('editor', 'enterer', 'reviewer', 'member')

    def setUp(self):
        super(TestPermissionForms, self).setUp()

        from datetime import date

        import transaction
        from occams import Session
        from occams_datastore import models as datastore

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            Session.info['blame'] = user
            Session.add(user)
            Session.flush()

            form_published = datastore.Schema(
                name=u'test_schema',
                title=u'test_title',
                publish_date=date(2015, 1, 1)
            )

            form_unpublished = datastore.Schema(
                name=u'test_schema2',
                title=u'test_title2',
            )

            Session.add_all([
                datastore.State(
                    name=u'pending-entry',
                    title=u'pending-entry'),
                datastore.State(
                    name=u'pending-review',
                    title=u'pending-review'),
                datastore.State(
                    name=u'pending-correction',
                    title=u'pending-correction'),
                datastore.State(
                    name=u'complete',
                    title=u'complete')
            ])

            Session.add(datastore.Attribute(
                name=u'test_field',
                title=u'test_title',
                description=u'test_desc',
                type=u'string',
                schema=form_published,
                order=0
            ))

            Session.add(datastore.Attribute(
                name=u'text_box2',
                title=u'text_box2',
                description=u'text_box_desc2',
                type=u'string',
                schema=form_published,
                order=1
            ))

            Session.add(datastore.Attribute(
                name=u'test_field2',
                title=u'test_title2',
                description=u'test_desc2',
                type=u'string',
                schema=form_unpublished,
                order=0
            ))

            Session.add(datastore.Attribute(
                name=u'text_box2',
                title=u'text_box2',
                description=u'text_box_desc2',
                type=u'string',
                schema=form_unpublished,
                order=1
            ))

            Session.flush()

    # tests for forms

    @data(*ALL_ALLOWED)
    def test_forms_view(self, group):
        url = '/forms'

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get(url, extra_environ=environ)
        self.assertEquals(200, response.status_code)

    def test_not_authenticated_forms(self):
        url = '/forms'
        response = self.app.get(url, status='*')
        self.assertEquals(401, response.status_code)

    @data(*ALL_ALLOWED)
    def test_forms_view_xhr(self, group):
        url = '/forms'

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get(url, extra_environ=environ, xhr=True)
        self.assertEquals(200, response.status_code)

    def test_not_authenticated_forms_xhr(self):
        url = '/forms'
        response = self.app.get(url, status='*', xhr=True)
        self.assertEquals(401, response.status_code)

    @data(*DEFAULT_ALLOWED)
    def test_forms_upload_json(self, group):
        import json

        url = '/forms?files'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        data = {
            'title': 'OMG',
            'storage': 'eav',
            'publish_date': '2015-05-26',
            "name": 'omg'
        }

        response = self.app.post(
            url,
            extra_environ=environ,
            status='*',
            upload_files=[('files', 'upload.json', json.dumps(data))],
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True)

        self.assertEquals(200, response.status_code)

    @data(*DEFAULT_NOT_ALLOWED)
    def test_not_allowed_forms_upload_json(self, group):
        import json

        url = '/forms?files'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        data = {
            'title': 'OMG',
            'storage': 'eav',
            'publish_date': '2015-05-26',
            "name": 'omg'
        }

        response = self.app.post(
            url,
            extra_environ=environ,
            status='*',
            upload_files=[('files', 'upload.json', json.dumps(data))],
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True)

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_files_upload(self):
        url = '/forms?files'
        response = self.app.post(url, status='*', xhr=True)
        self.assertEquals(401, response.status_code)

    @data(*DEFAULT_ALLOWED)
    def test_forms_add_json_validate(self, group):
        url = '/forms?validate'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        data = {
            'name': u'test_form',
            'title': u'test_form',
            'versions': [],
            'isNew': True,
            'hasVersions': False
        }

        response = self.app.get(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True,
            params=data)

        self.assertEquals(200, response.status_code)

    @data(*DEFAULT_NOT_ALLOWED)
    def test_not_allowed_forms_add_json_validate(self, group):
        url = '/forms?validate'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        data = {
            'name': u'test_form',
            'title': u'test_form',
            'versions': [],
            'isNew': True,
            'hasVersions': False
        }

        response = self.app.get(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True,
            params=data)

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_validate_field(self):
        url = '/forms?validate'

        response = self.app.get(url, status='*', xhr=True)
        self.assertEquals(401, response.status_code)

    @data(*DEFAULT_ALLOWED)
    def test_forms_add(self, group):
        url = '/forms'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        data = {
            'name': 'test_form',
            'title': 'test_form',
            'versions': [],
            'isNew': True,
            'hasVersions': False
        }

        response = self.app.post_json(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        self.assertEquals(200, response.status_code)

    @data(*DEFAULT_NOT_ALLOWED)
    def test_not_allowed_forms_add(self, group):
        url = '/forms'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        data = {
            'name': 'test_form',
            'title': 'test_form',
            'versions': [],
            'isNew': True,
            'hasVersions': False
        }

        response = self.app.post_json(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_forms_add(self):
        url = '/forms'
        response = self.app.post_json(url, status='*')
        self.assertEquals(401, response.status_code)

    # tests for workflows

    @data(*ALL_ALLOWED)
    def test_forms_workflows(self, group):
        url = '/forms/workflows/default'

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get(url, extra_environ=environ)
        self.assertEquals(200, response.status_code)

    def test_not_authenticated_workflows_default(self):
        url = '/forms/workflows/default'
        response = self.app.get(url, status='*')
        self.assertEquals(401, response.status_code)

    # test for versions

    @data(*ALL_ALLOWED)
    def test_forms_versions(self, group):
        url = '/forms/test_schema/versions/2015-01-01'

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get(url, extra_environ=environ)
        self.assertEquals(200, response.status_code)

    def test_not_authenticated_versions(self):
        url = '/forms/test_schema/versions/2015-01-01'
        response = self.app.get(url, status='*')
        self.assertEquals(401, response.status_code)

    @data(*ALL_ALLOWED)
    def test_forms_versions_xhr(self, group):
        # test same url with xhr
        url = '/forms/test_schema/versions/2015-01-01'

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get(url, extra_environ=environ, xhr=True)
        self.assertEquals(200, response.status_code)

    def test_not_authenticated_versions_xhr(self):
        url = '/forms/test_schema/versions/2015-01-01'
        response = self.app.get(url, status='*', xhr=True)
        self.assertEquals(401, response.status_code)

    @data(*ALL_ALLOWED)
    def test_forms_versions_download_json(self, group):
        url = '/forms/test_schema/versions/2015-01-01?download=json'

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get(url, extra_environ=environ)
        self.assertEquals(200, response.status_code)

    def test_not_authenticated_versions_download_json(self):
        url = '/forms/test_schema/versions/2015-01-01?download=json'
        response = self.app.get(url, status='*')
        self.assertEquals(401, response.status_code)

    # tests for versions preview

    @data(*ALL_ALLOWED)
    def test_forms_versions_preview(self, group):
        url = '/forms/test_schema/versions/2015-01-01/preview'

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get(url, extra_environ=environ)
        self.assertEquals(200, response.status_code)

    def test_not_authenticated_preview(self):
        url = '/forms/test_schema/versions/2015-01-01/preview'
        response = self.app.get(url, status='*')
        self.assertEquals(401, response.status_code)

    @data(*ALL_ALLOWED)
    def test_forms_versions_preview_post(self, group):
        url = '/forms/test_schema/versions/2015-01-01/preview'

        data = {}

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.post(
            url,
            extra_environ=environ,
            status='*',
            params=data)

        self.assertEquals(200, response.status_code)

    def test_not_authenticated_preview_post(self):
        url = '/forms/test_schema/versions/2015-01-01/preview'
        response = self.app.post(url, status='*')
        self.assertEquals(401, response.status_code)

    # tests for version edit

    @data(*ALLOWED_NO_EDITOR)
    def test_forms_versions_edit(self, group):
        url = '/forms/test_schema/versions/2015-01-01'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        data = {
            '__url__': url,
            'name': 'test_schema',
            'title': 'test_title',
            'fields': [],
            'hasFields': False,
            'isNew': False,
            'publish_date': '2015-01-01'
        }

        response = self.app.put_json(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        self.assertEquals(200, response.status_code)

    @data(*NOT_ALLOWED_W_EDITOR)
    def test_not_allowed_forms_versions_edit(self, group):
        url = '/forms/test_schema/versions/2015-01-01'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        data = {
            '__url__': url,
            'name': 'test_schema',
            'title': 'test_title',
            'fields': [],
            'hasFields': False,
            'isNew': False,
            'publish_date': '2015-01-01'
        }

        response = self.app.put_json(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_versions_edit(self):
        url = '/forms/test_schema/versions/2015-01-01'
        response = self.app.put_json(url, status='*')
        self.assertEquals(401, response.status_code)

    @data(*DEFAULT_ALLOWED)
    def test_forms_versions_edit_unpublished(self, group):
        from occams import Session
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        form_id = Session.query(datastore.Schema.id).filter(
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

        response = self.app.put_json(
            url.format(form_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        self.assertEquals(200, response.status_code)

    @data(*DEFAULT_NOT_ALLOWED)
    def test_not_allowed_forms_versions_edit_unpublished(self, group):
        from occams import Session
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        form_id = Session.query(datastore.Schema.id).filter(
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

        response = self.app.put_json(
            url.format(form_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_versions_edit_unpublished(self):
        from occams import Session
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}'

        form_id = Session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        response = self.app.put_json(url.format(form_id), status='*')
        self.assertEquals(401, response.status_code)

    @data(*ALLOWED_NO_EDITOR)
    def test_forms_versions_edit_publish(self, group):
        url = '/forms/test_schema/versions/2015-01-01?publish'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        data = {
            '__url__': url,
            'name': 'test_schema',
            'title': 'test_title',
            'fields': [],
            'hasFields': False,
            'isNew': False,
            'publish_date': '2015-01-01'
        }

        response = self.app.put_json(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        self.assertEquals(200, response.status_code)

    @data(*NOT_ALLOWED_W_EDITOR)
    def test_not_allowed_forms_versions_edit_publish(self, group):
        url = '/forms/test_schema/versions/2015-01-01?publish'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        data = {
            '__url__': url,
            'name': 'test_schema',
            'title': 'test_title',
            'fields': [],
            'hasFields': False,
            'isNew': False,
            'publish_date': '2015-01-01'
        }

        response = self.app.put_json(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_versions_edit_publish(self):
        url = '/forms/test_schema/versions/2015-01-01?publish'
        response = self.app.put_json(url, status='*')
        self.assertEquals(401, response.status_code)

    @data(*DEFAULT_ALLOWED)
    def test_forms_versions_post_draft(self, group):
        url = '/forms/test_schema/versions/2015-01-01?draft'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        data = {
            '__url__': url,
            'name': 'test_schema',
            'title': 'test_title',
            'fields': [],
            'hasFields': False,
            'isNew': False,
            'publish_date': '2015-01-01'
        }

        response = self.app.post(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True,
            params=data)

        self.assertEquals(200, response.status_code)

    @data(*DEFAULT_NOT_ALLOWED)
    def test_not_allowed_forms_versions_post_draft(self, group):
        url = '/forms/test_schema/versions/2015-01-01?draft'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        data = {
            '__url__': url,
            'name': 'test_schema',
            'title': 'test_title',
            'fields': [],
            'hasFields': False,
            'isNew': False,
            'publish_date': '2015-01-01'
        }

        response = self.app.post(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True,
            params=data)

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_versions_post_draft(self):
        url = '/forms/test_schema/versions/2015-01-01?draft'
        response = self.app.post(url, status='*')
        self.assertEquals(401, response.status_code)

    # test forms version editor

    @data(*ALLOWED_NO_EDITOR)
    def test_forms_versions_editor(self, group):
        url = '/forms/test_schema/versions/2015-01-01/editor'

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get(url, extra_environ=environ, status='*')
        self.assertEquals(200, response.status_code)

    @data(*NOT_ALLOWED_W_EDITOR)
    def test_not_allowed_forms_versions_editor(self, group):
        url = '/forms/test_schema/versions/2015-01-01/editor'

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.delete(url, extra_environ=environ, status='*')
        self.assertEquals(403, response.status_code)

    def test_not_authenticated_versions_editor(self):
        url = '/forms/test_schema/versions/2015-01-01/editor'
        response = self.app.get(url, status='*')
        self.assertEquals(401, response.status_code)

    @data(*DEFAULT_ALLOWED)
    def test_forms_versions_editor_unpublished(self, group):
        from occams import Session
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/editor'

        environ = self.make_environ(userid=USERID, groups=[group])

        form_id = Session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        response = self.app.get(
            url.format(form_id), extra_environ=environ, status='*')

        self.assertEquals(200, response.status_code)

    @data(*DEFAULT_NOT_ALLOWED)
    def test_not_allowed_forms_versions_editor_unpublished(self, group):
        from occams import Session
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/editor'

        environ = self.make_environ(userid=USERID, groups=[group])

        form_id = Session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        response = self.app.get(
            url.format(form_id), extra_environ=environ, status='*')

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_versions_editor_unpublished(self):
        from occams import Session
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/editor'

        form_id = Session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        response = self.app.get(url.format(form_id), status='*')
        self.assertEquals(401, response.status_code)

    # test forms version delete

    @data(*ALLOWED_NO_EDITOR)
    def test_forms_versions_delete(self, group):
        url = '/forms/test_schema/versions/2015-01-01'
        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)
        response = self.app.delete(
            url,
            extra_environ=environ,
            xhr=True,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            }
        )

        self.assertEquals(200, response.status_code)

    @data(*NOT_ALLOWED_W_EDITOR)
    def test_not_allowed_forms_versions_delete(self, group):
        url = '/forms/test_schema/versions/2015-01-01'
        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)
        response = self.app.delete(
            url,
            extra_environ=environ,
            xhr=True,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            }
        )

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_versions_delete(self):
        url = '/forms/test_schema/versions/2015-01-01'
        response = self.app.delete(url, status='*')
        self.assertEquals(401, response.status_code)

    @data(*DEFAULT_ALLOWED)
    def test_forms_versions_delete_unpublished(self, group):
        from occams import Session
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}'
        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        form_id = Session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        response = self.app.delete(
            url.format(form_id),
            extra_environ=environ,
            xhr=True,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            }
        )

        self.assertEquals(200, response.status_code)

    @data(*DEFAULT_NOT_ALLOWED)
    def test_not_allowed_forms_versions_delete_unpublished(self, group):
        from occams import Session
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}'
        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        form_id = Session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        response = self.app.delete(
            url.format(form_id),
            extra_environ=environ,
            xhr=True,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            }
        )

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_versions_unpublished_delete(self):
        from occams import Session
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}'

        form_id = Session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        response = self.app.delete(url.format(form_id), status='*')
        self.assertEquals(401, response.status_code)

    # tests for fields

    @data(*ALL_ALLOWED)
    def test_view_field_json(self, group):
        url = '/forms/test_schema/versions/2015-01-01/fields/test_field'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        response = self.app.get(
            url,
            status='*',
            xhr=True,
            extra_environ=environ,
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            })
        self.assertEquals(200, response.status_code)

    def test_not_authenticated_view_field_json(self):
        url = '/forms/test_schema/versions/2015-01-01/fields/test_field'

        response = self.app.delete(url, status='*', xhr=True)
        self.assertEquals(401, response.status_code)

    @data(*ALLOWED_NO_EDITOR)
    def test_move_field(self, group):
        url = '/forms/test_schema/versions/2015-01-01/fields/text_box2?move'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        data = {
            'index': 0
        }

        response = self.app.put_json(
            url,
            status='*',
            extra_environ=environ,
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        self.assertEquals(200, response.status_code)

    @data(*NOT_ALLOWED_W_EDITOR)
    def test_not_allowed_move_field(self, group):
        url = '/forms/test_schema/versions/2015-01-01/fields/text_box2?move'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        data = {
            'index': 0
        }

        response = self.app.put_json(
            url,
            status='*',
            extra_environ=environ,
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_move_field(self):
        url = '/forms/test_schema/versions/2015-01-01/fields/text_box2?move'

        response = self.app.put(url, status='*', xhr=True)
        self.assertEquals(401, response.status_code)

    @data(*DEFAULT_ALLOWED)
    def test_move_field_unpublished(self, group):
        from occams import Session
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/fields/text_box2?move'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        form_id = Session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        data = {
            'index': 0
        }

        response = self.app.put_json(
            url.format(form_id),
            status='*',
            extra_environ=environ,
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        self.assertEquals(200, response.status_code)

    @data(*DEFAULT_NOT_ALLOWED)
    def test_not_allowed_move_field_unpublished(self, group):
        from occams import Session
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/fields/text_box2?move'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        form_id = Session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        data = {
            'index': 0
        }

        response = self.app.put_json(
            url.format(form_id),
            status='*',
            extra_environ=environ,
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_move_field_unpublished(self):
        from occams import Session
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/fields/text_box2?move'

        form_id = Session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        response = self.app.put(url.format(form_id), status='*', xhr=True)
        self.assertEquals(401, response.status_code)

    @data(*DEFAULT_ALLOWED)
    def test_add_field(self, group):
        url = '/forms/test_schema/versions/2015-01-01/fields'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

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

        response = self.app.post_json(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data
        )

        self.assertEquals(200, response.status_code)

    @data(*DEFAULT_NOT_ALLOWED)
    def test_not_allowed_add_field(self, group):
        url = '/forms/test_schema/versions/2015-01-01/fields'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

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

        response = self.app.post_json(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data
        )

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_add_field(self):
        url = '/forms/test_schema/versions/2015-01-01/fields'
        response = self.app.post(url, status='*', xhr=True)
        self.assertEquals(401, response.status_code)

    @data(*ALLOWED_NO_EDITOR)
    def test_edit_field(self, group):
        url = '/forms/test_schema/versions/2015-01-01/fields/test_field'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        data = {
            'name': 'test_field_add',
            'type': 'string',
            'title': 'updated title'
        }

        response = self.app.put_json(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data
        )

        self.assertEquals(200, response.status_code)

    @data(*NOT_ALLOWED_W_EDITOR)
    def test_not_allowed_edit_field(self, group):
        url = '/forms/test_schema/versions/2015-01-01/fields/test_field'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        data = {
            'name': 'test_field_add',
            'type': 'string',
            'title': 'updated title'
        }

        response = self.app.put_json(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data
        )

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_edit_field(self):
        url = '/forms/test_schema/versions/2015-01-01/fields/test_field'
        response = self.app.put(url, status='*', xhr=True)
        self.assertEquals(401, response.status_code)

    @data(*DEFAULT_ALLOWED)
    def test_edit_field_unpublished(self, group):
        from occams import Session
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/fields/test_field2'

        form_id = Session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        data = {
            'name': 'test_field_add',
            'type': 'string',
            'title': 'updated title'
        }

        response = self.app.put_json(
            url.format(form_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data
        )

        self.assertEquals(200, response.status_code)

    @data(*DEFAULT_NOT_ALLOWED)
    def test_not_allowed_edit_field_unpublished(self, group):
        from occams import Session
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/fields/test_field2'

        form_id = Session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        data = {
            'name': 'test_field_add',
            'type': 'string',
            'title': 'updated title'
        }

        response = self.app.put_json(
            url.format(form_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data
        )

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_edit_field_unpublised(self):
        from occams import Session
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/fields/test_field2'

        form_id = Session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        response = self.app.put(url.format(form_id), status='*', xhr=True)
        self.assertEquals(401, response.status_code)

    @data(*ALLOWED_NO_EDITOR)
    def test_edit_validate_fields(self, group):
        url = '/forms/test_schema/versions/2015-01-01/fields?validate'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

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

        response = self.app.put_json(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data
        )

        self.assertEquals(200, response.status_code)

    @data(*NOT_ALLOWED_W_EDITOR)
    def test_not_allowed_edit_validate_fields(self, group):
        url = '/forms/test_schema/versions/2015-01-01/fields?validate'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

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

        response = self.app.put_json(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data
        )

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_edit_validate_fields(self):
        url = '/forms/test_schema/versions/2015-01-01/fields?validate'

        response = self.app.put(url, status='*', xhr=True)
        self.assertEquals(401, response.status_code)

    @data(*DEFAULT_ALLOWED)
    def test_edit_validate_fields_unpublished(self, group):
        from occams import Session
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/fields?validate'

        form_id = Session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

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

        response = self.app.put_json(
            url.format(form_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data
        )

        self.assertEquals(200, response.status_code)

    @data(*DEFAULT_NOT_ALLOWED)
    def test_not_allowed_edit_validate_fields_unpublished(self, group):
        from occams import Session
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/fields?validate'

        form_id = Session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

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

        response = self.app.put_json(
            url.format(form_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data
        )

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_edit_validate_fields_unpublished(self):
        from occams import Session
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/fields?validate'

        form_id = Session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        response = self.app.put(url.format(form_id), status='*', xhr=True)
        self.assertEquals(401, response.status_code)

    @data(*ALLOWED_NO_EDITOR)
    def test_edit_validate_field(self, group):
        url = '/forms/test_schema/versions/2015-01-01/fields/' \
              'test_field?validate'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        response = self.app.get(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            }
        )

        self.assertEquals(200, response.status_code)

    @data(*NOT_ALLOWED_W_EDITOR)
    def test_not_allowed_edit_validate_field(self, group):
        url = '/forms/test_schema/versions/2015-01-01/fields/' \
              'test_field?validate'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        response = self.app.get(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            }
        )

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_edit_validate_field(self):
        url = '/forms/test_schema/versions/2015-01-01/fields/' \
              'test_field?validate'

        environ = self.make_environ(userid=USERID)
        csrf_token = self.get_csrf_token(environ)

        response = self.app.get(
            url,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            }
        )

        self.assertEquals(401, response.status_code)

    @data(*DEFAULT_ALLOWED)
    def test_edit_validate_field_unpublished(self, group):
        from occams import Session
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/fields/' \
              'test_field2?validate'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        form_id = Session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        response = self.app.get(
            url.format(form_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            }
        )

        self.assertEquals(200, response.status_code)

    @data(*DEFAULT_NOT_ALLOWED)
    def test_not_allowed_edit_validate_field_unpublished(self, group):
        from occams import Session
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/fields/' \
              'test_field2?validate'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        form_id = Session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        response = self.app.get(
            url.format(form_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            }
        )

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_edit_validate_field_unpublished(self):
        from occams import Session
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/fields/' \
              'test_field2?validate'

        environ = self.make_environ(userid=USERID)
        csrf_token = self.get_csrf_token(environ)

        form_id = Session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        response = self.app.get(
            url.format(form_id),
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            }
        )

        self.assertEquals(401, response.status_code)

    @data(*ALLOWED_NO_EDITOR)
    def test_delete_field(self, group):
        url = '/forms/test_schema/versions/2015-01-01/fields/test_field'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        response = self.app.delete(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True
        )

        self.assertEquals(200, response.status_code)

    @data(*NOT_ALLOWED_W_EDITOR)
    def test_not_allowed_delete_field(self, group):
        url = '/forms/test_schema/versions/2015-01-01/fields/test_field'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        response = self.app.delete(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True
        )

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_delete_field(self):
        url = '/forms/test_schema/versions/2015-01-01/fields/test_field'

        response = self.app.delete(url, status='*', xhr=True)
        self.assertEquals(401, response.status_code)

    @data(*DEFAULT_ALLOWED)
    def test_delete_field_unpublished(self, group):
        from occams import Session
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/fields/test_field2'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        form_id = Session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        response = self.app.delete(
            url.format(form_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True
        )

        self.assertEquals(200, response.status_code)

    @data(*DEFAULT_NOT_ALLOWED)
    def test_not_allowed_delete_field_unpublished(self, group):
        from occams import Session
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/fields/test_field2'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        form_id = Session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        response = self.app.delete(
            url.format(form_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True
        )

        self.assertEquals(403, response.status_code)

    def test_not_authenticated_delete_field_unpublished(self):
        from occams import Session
        from occams_datastore import models as datastore

        url = '/forms/test_schema2/versions/{}/fields/test_field2'

        form_id = Session.query(datastore.Schema.id).filter(
            datastore.Schema.name == u'test_schema2').scalar()

        response = self.app.delete(url.format(form_id), status='*', xhr=True)

        self.assertEquals(401, response.status_code)
