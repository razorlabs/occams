from ddt import ddt, data

from tests import FunctionalFixture


@ddt
class TestPermissionsStudyList(FunctionalFixture):

    url = '/studies'

    @data('administrator', 'investigator', 'statistician', 'researcher',
          'nurse', 'assistant', 'student', None)
    def test_allowed(self, group):
        environ = self.make_environ(groups=[group])
        self.app.get(self.url, extra_environ=environ, status=200)

    def test_not_authenticated(self):
        self.app.get(self.url, status=403)
