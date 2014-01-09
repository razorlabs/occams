from bs4 import BeautifulSoup
from ddt import ddt, data

from tests import ViewFixture, make_environ


@ddt
class TestList(ViewFixture):

    @data('administrator', 'investigator', 'statistician', 'researcher',
          'nurse')
    def test_view_allowed(self, principal):
        ENVIRON = make_environ(groups=[principal])
        response = self.app.get('/data', extra_environ=ENVIRON)
        self.assertEqual(200, response.status_code)

    @data('assistant', 'student', None)
    def test_view_not_allowed(self, principal):
        ENVIRON = make_environ(groups=[principal])
        response = self.app.get('/data', extra_environ=ENVIRON, status='*')
        self.assertIn(response.status_code, (401, 403))

    def test_not_authenticated(self):
        response = self.app.get('/data', status='*')
        self.assertIn(response.status_code, (401, 403))
