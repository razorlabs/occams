from bs4 import BeautifulSoup
from nose.tools import set_trace

from tests import ViewFixture, make_environ


class TestList(ViewFixture):

    def test_view(self):
        ENVIRON = make_environ(groups=['administrators'])
        response = self.app.get('/data', extra_environ=ENVIRON)
        self.assertEqual(200, response.status_code)
