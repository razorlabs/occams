from ddt import ddt, data

from tests import FunctionalFixture


@ddt
class TestPermissionsHome(FunctionalFixture):

    url = '/'

    @data('administrator', 'investigator', 'statistician', 'researcher',
          'nurse', 'assistant', 'student', None)
    def test_allowed(self, group):
        environ = self.make_environ(groups=[group])
        response = self.app.get(self.url, extra_environ=environ, status='*')
        self.assertNotEqual(response.status_code, 403)

    def test_not_authenticated(self):
        response = self.app.get(self.url, status='*')
        self.assertIn('login', response.body)
