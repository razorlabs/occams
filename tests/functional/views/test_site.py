import pytest
from tests.testing import USERID, make_environ


class TestPermissionsSiteList:

    url = '/studies/sites'

    @pytest.fixture(autouse=True)
    def populate(self, app, dbsession):
        import transaction
        from occams import models

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            blame = models.User(key=USERID)
            dbsession.info['blame'] = blame
            dbsession.add(blame)
            dbsession.flush()

            dbsession.add(models.Site(name=u'ucsd', title=u'UCSD'))
            dbsession.add(models.Site(name=u'ucla', title=u'UCSD'))

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'ucsd:enterer', 'ucsd:reviewer',
        'ucsd:consumer', 'ucla:member', 'ucsd:member', None])
    def test_allowed(self, app, dbsession, group):
        environ = make_environ(userid=USERID, groups=[group])
        res = app.get(
            self.url, extra_environ=environ, xhr=True, status='*')
        assert 200 == res.status_code

    def test_filtered_site(self, app, dbsession):
        """
        Any authenticated user can view a site resources, but the listing
        is filterd based on what sites they have access.
        """
        environ = make_environ(userid=USERID, groups=['ucsd:member'])
        res = app.get(
            self.url, extra_environ=environ, xhr=True, status='*')
        assert 200 == res.status_code
        assert all('ucsd' == s['name'] for s in res.json['sites'])

    def test_not_authenticated(self, app, dbsession):
        res = app.get(self.url, xhr=True, status='*')
        assert 401 == res.status_code
