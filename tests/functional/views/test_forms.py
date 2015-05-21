from ddt import ddt, data

from tests import FunctionalFixture, USERID


@ddt
class TestPermissionForms(FunctionalFixture):
    def setUp(self):
        super(TestPermissionForms, self).setUp()

        from datetime import date

        import transaction
        from occams import Session
        from occams_studies import models as forms
        from occams_datastore import models as datastore

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            Session.info['blame'] = user
            Session.add(user)
            Session.flush()

            form = datastore.Schema(
                name=u'test_schema',
                title=u'test_title',
                publish_date=date(2015, 1, 1)
            )

            Session.add(form)
            Session.flush()

    @data('administrator')
    def test_forms_view(self, group):
        url = '/forms'

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get(url, extra_environ=environ)
        self.assertEquals(200, response.status_code)

    @data('administrator')
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

    @data('member')
    def test_forms_add_not_allowed(self, group):
        url = '/forms'

        environ = self.make_environ(userid=USERID, groups=[group])
        csrf_token = self.get_csrf_token(environ)

        response = self.app.post_json(
            url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params={})

        self.assertEquals(403, response.status_code)

    @data('administrator')
    def test_forms_workflows(self, group):
        url = '/forms/workflows/default'

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get(url, extra_environ=environ)
        self.assertEquals(200, response.status_code)

    def test_not_authenticated(self):
        url = '/forms'
        response = self.app.get(url, status='*')
        self.assertEquals(401, response.status_code)
