from ddt import ddt, data

from tests import FunctionalFixture, USERID


@ddt
class TestPermissionsStudyList(FunctionalFixture):

    url = '/studies'

    def setUp(self):
        super(TestPermissionsStudyList, self).setUp()

        import transaction
        from occams import Session
        from occams_datastore import models as datastore

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            Session.add(datastore.User(key=USERID))

    @data('administrator', 'investigator', 'statistician', 'researcher',
          'nurse', 'assistant', 'student', None)
    def test_allowed(self, group):
        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get(self.url, extra_environ=environ)
        self.assertEquals(200, response.status_code)

    def test_not_authenticated(self):
        self.app.get(self.url, status=403)
