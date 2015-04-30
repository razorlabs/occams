from ddt import ddt, data

from tests import FunctionalFixture, USERID


@ddt
class TestPermissionsSiteList(FunctionalFixture):

    url = '/studies/sites'

    def setUp(self):
        super(TestPermissionsSiteList, self).setUp()

        import transaction
        from occams import Session
        from occams_datastore import models as datastore
        from occams_studies import models as studies

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            blame = datastore.User(key=USERID)
            Session.info['blame'] = blame
            Session.add(blame)
            Session.flush()

            Session.add(studies.Site(name=u'ucsd', title=u'UCSD'))
            Session.add(studies.Site(name=u'ucla', title=u'UCSD'))

    @data('administrator', 'manager', 'ucsd:enterer', 'ucsd:reviewer',
          'ucsd:consumer', 'ucla:member', 'ucsd:member', None)
    def test_allowed(self, group):
        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get(
            self.url, extra_environ=environ, xhr=True, status='*')
        self.assertEquals(200, response.status_code)

    def test_filtered_site(self):
        """
        Any authenticated user can view a site resources, but the listing
        is filterd based on what sites they have access.
        """
        environ = self.make_environ(userid=USERID, groups=['ucsd:member'])
        response = self.app.get(
            self.url, extra_environ=environ, xhr=True, status='*')
        self.assertEquals(200, response.status_code)
        self.assertTrue(
            all('ucsd' == s['name'] for s in response.json['sites']))

    def test_not_authenticated(self):
        response = self.app.get(self.url, xhr=True, status='*')
        self.assertEquals(401, response.status_code)
