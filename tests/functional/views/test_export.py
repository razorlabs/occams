from ddt import ddt, data

from tests import FunctionalFixture


@ddt
class TestPermissionsAbout(FunctionalFixture):

    url = '/exports'

    @data('administrator', 'investigator', 'statistician', 'researcher',
          'nurse')
    def test_allowed(self, group):
        environ = self.make_environ(groups=[group])
        response = self.app.get(self.url, extra_environ=environ, status='*')
        self.assertNotEqual(response.status_code, 403)

    @data('assistant', 'student', None)
    def test_not_allowed(self, group):
        environ = self.make_environ(groups=[group])
        response = self.app.get(self.url, extra_environ=environ, status='*')
        self.assertEqual(response.status_code, 403)

    def test_not_authenticated(self):
        response = self.app.get(self.url, status='*')
        self.assertIn('login', response.body)


@ddt
class TestExportViewPermissionsFaq(FunctionalFixture):

    url = '/exports/faq'

    @data('administrator', 'investigator', 'statistician', 'researcher',
          'nurse')
    def test_allowed(self, group):
        environ = self.make_environ(groups=[group])
        response = self.app.get(self.url, extra_environ=environ, status='*')
        self.assertNotEqual(response.status_code, 403)

    @data('assistant', 'student', None)
    def test_not_allowed(self, group):
        environ = self.make_environ(groups=[group])
        response = self.app.get(self.url, extra_environ=environ, status='*')
        self.assertEqual(response.status_code, 403)

    def test_not_authenticated(self):
        response = self.app.get(self.url, status='*')
        self.assertIn('login', response.body)


@ddt
class TestPermissionsAdd(FunctionalFixture):

    url = '/exports/add'

    @data('administrator', 'investigator', 'statistician', 'researcher',
          'nurse')
    def test_allowed(self, group):
        environ = self.make_environ(groups=[group])
        response = self.app.get(self.url, extra_environ=environ, status='*')
        self.assertNotEqual(response.status_code, 403)

    @data('assistant', 'student', None)
    def test_not_allowed(self, group):
        environ = self.make_environ(groups=[group])
        response = self.app.get(self.url, extra_environ=environ, status='*')
        self.assertEqual(response.status_code, 403)

    def test_not_authenticated(self):
        response = self.app.get(self.url, status='*')
        self.assertIn('login', response.body)


@ddt
class TestPermissionsStatus(FunctionalFixture):

    url = '/exports/status'

    @data('administrator', 'investigator', 'statistician', 'researcher',
          'nurse')
    def test_allowed(self, group):
        environ = self.make_environ(groups=[group])
        response = self.app.get(self.url, extra_environ=environ, status='*')
        self.assertNotEqual(response.status_code, 403)

    @data('assistant', 'student', None)
    def test_not_allowed(self, group):
        environ = self.make_environ(groups=[group])
        response = self.app.get(self.url, extra_environ=environ, status='*')
        self.assertEqual(response.status_code, 403)

    def test_not_authenticated(self):
        response = self.app.get(self.url, status='*')
        self.assertIn('login', response.body)


@ddt
class TestPermissionsStatusJSON(FunctionalFixture):

    url = '/exports/status'

    @data('administrator', 'investigator', 'statistician', 'researcher',
          'nurse')
    def test_allowed(self, group):
        environ = self.make_environ(groups=[group])
        response = self.app.get(
            self.url, extra_environ=environ, xhr=True, status='*')
        self.assertNotEqual(response.status_code, 403)

    @data('assistant', 'student', None)
    def test_not_allowed(self, group):
        environ = self.make_environ(groups=[group])
        response = self.app.get(
            self.url, extra_environ=environ, xhr=True, status='*')
        self.assertEqual(response.status_code, 403)

    def test_not_authenticated(self):
        response = self.app.get(self.url, xhr=True, status='*')
        self.assertIn('login', response.body)


@ddt
class TestPersmissionsDelete(FunctionalFixture):

    url = '/exports/123/delete'

    @data('administrator', 'investigator', 'statistician', 'researcher',
          'nurse')
    def test_allowed(self, group):
        environ = self.make_environ(groups=[group])
        response = self.app.post(
            self.url, extra_environ=environ, xhr=True, status='*')
        self.assertNotEqual(response.status_code, 403)

    @data('assistant', 'student', None)
    def test_not_allowed(self, group):
        environ = self.make_environ(groups=[group])
        response = self.app.post(
            self.url, extra_environ=environ, xhr=True, status='*')
        self.assertEqual(response.status_code, 403)

    def test_not_authenticated(self):
        response = self.app.post(self.url, xhr=True, status='*')
        self.assertIn('login', response.body)


@ddt
class TestPersmissionsCodebook(FunctionalFixture):

    url = '/exports/codebook'

    @data('administrator', 'investigator', 'statistician', 'researcher',
          'nurse')
    def test_allowed(self, group):
        environ = self.make_environ(groups=[group])
        response = self.app.get(
            self.url, extra_environ=environ, status='*')
        self.assertNotEqual(response.status_code, 403)

    @data('assistant', 'student', None)
    def test_not_allowed(self, group):
        environ = self.make_environ(groups=[group])
        response = self.app.get(
            self.url, extra_environ=environ, status='*')
        self.assertEqual(response.status_code, 403)

    def test_not_authenticated(self):
        response = self.app.get(self.url, status='*')
        self.assertIn('login', response.body)


@ddt
class TestPersmissionsCodebookJSON(FunctionalFixture):

    url = '/exports/codebook'

    @data('administrator', 'investigator', 'statistician', 'researcher',
          'nurse')
    def test_allowed(self, group):
        environ = self.make_environ(groups=[group])
        response = self.app.get(
            self.url, extra_environ=environ, xhr=True, status='*')
        self.assertNotEqual(response.status_code, 403)

    @data('assistant', 'student', None)
    def test_not_allowed(self, group):
        environ = self.make_environ(groups=[group])
        response = self.app.get(
            self.url, extra_environ=environ, xhr=True, status='*')
        self.assertEqual(response.status_code, 403)

    def test_not_authenticated(self):
        response = self.app.get(self.url, xhr=True, status='*')
        self.assertIn('login', response.body)


@ddt
class TestPersmissionsCodebookDownload(FunctionalFixture):

    url = '/exports/codebook/download'

    @data('administrator', 'investigator', 'statistician', 'researcher',
          'nurse')
    def test_allowed(self, group):
        environ = self.make_environ(groups=[group])
        response = self.app.get(
            self.url, extra_environ=environ, status='*')
        self.assertNotEqual(response.status_code, 403)

    @data('assistant', 'student', None)
    def test_not_allowed(self, group):
        environ = self.make_environ(groups=[group])
        response = self.app.get(
            self.url, extra_environ=environ, status='*')
        self.assertEqual(response.status_code, 403)

    def test_not_authenticated(self):
        response = self.app.get(self.url, status='*')
        self.assertIn('login', response.body)


@ddt
class TestPersmissionsDownload(FunctionalFixture):

    url = '/exports/123/download'

    @data('administrator', 'investigator', 'statistician', 'researcher',
          'nurse')
    def test_allowed(self, group):
        environ = self.make_environ(groups=[group])
        response = self.app.get(
            self.url, extra_environ=environ, status='*')
        self.assertNotEqual(response.status_code, 403)

    @data('assistant', 'student', None)
    def test_not_allowed(self, group):
        environ = self.make_environ(groups=[group])
        response = self.app.get(
            self.url, extra_environ=environ, status='*')
        self.assertEqual(response.status_code, 403)

    def test_not_authenticated(self):
        response = self.app.get(self.url, status='*')
        self.assertIn('login', response.body)
