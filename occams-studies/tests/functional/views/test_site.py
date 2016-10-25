import pytest
from occams.testing import USERID, make_environ


class TestPermissionsSiteList:

    url = '/studies/sites'

    @pytest.fixture(autouse=True)
    def populate(self, app, db_session):
        import transaction
        from occams_datastore import models as datastore
        from occams_studies import models as studies

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            blame = datastore.User(key=USERID)
            db_session.info['blame'] = blame
            db_session.add(blame)
            db_session.flush()

            db_session.add(studies.Site(name=u'ucsd', title=u'UCSD'))
            db_session.add(studies.Site(name=u'ucla', title=u'UCSD'))

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'ucsd:enterer', 'ucsd:reviewer',
        'ucsd:consumer', 'ucla:member', 'ucsd:member', None])
    def test_allowed(self, app, db_session, group):
        environ = make_environ(userid=USERID, groups=[group])
        res = app.get(
            self.url, extra_environ=environ, xhr=True, status='*')
        assert 200 == res.status_code

    def test_filtered_site(self, app, db_session):
        """
        Any authenticated user can view a site resources, but the listing
        is filterd based on what sites they have access.
        """
        environ = make_environ(userid=USERID, groups=['ucsd:member'])
        res = app.get(
            self.url, extra_environ=environ, xhr=True, status='*')
        assert 200 == res.status_code
        assert all('ucsd' == s['name'] for s in res.json['sites'])

    def test_not_authenticated(self, app, db_session):
        res = app.get(self.url, xhr=True, status='*')
        assert 401 == res.status_code
