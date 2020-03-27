import pytest
from tests.testing import USERID, make_environ


class TestPermissionsSiteList:

    url = '/studies/sites'

    @pytest.fixture(autouse=True)
    def populate(self, app, using_dbsession):
        from occams import models
        with using_dbsession(app) as dbsession:
            dbsession.add(models.Site(name=u'ucsd', title=u'UCSD'))
            dbsession.add(models.Site(name=u'ucla', title=u'UCSD'))

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'ucsd:enterer', 'ucsd:reviewer',
        'ucsd:consumer', 'ucla:member', 'ucsd:member', None])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        res = testapp.get(
            self.url, extra_environ=environ, xhr=True, status='*')
        assert 200 == res.status_code

    def test_filtered_site(self, testapp):
        """
        Any authenticated user can view a site resources, but the listing
        is filterd based on what sites they have access.
        """
        environ = make_environ(userid=USERID, groups=['ucsd:member'])
        res = testapp.get(
            self.url, extra_environ=environ, xhr=True, status='*')
        assert 200 == res.status_code
        assert all('ucsd' == s['name'] for s in res.json['sites'])

    def test_not_authenticated(self, testapp):
        res = testapp.get(self.url, xhr=True, status='*')
        assert 401 == res.status_code
