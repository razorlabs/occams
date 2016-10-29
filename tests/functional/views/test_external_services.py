import pytest
from occams.testing import USERID, make_environ


class TestManageExternalServices:

    url = '/studies/test_study/manage-external-services'

    @pytest.fixture(autouse=True)
    def transact(app, dbsession, factories):
        import transaction

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            dbsession.info['blame'] = factories.UserFactory.create(key=USERID)
            dbsession.flush()

            factories.StudyFactory.create(
                name='test_study'
            )

            dbsession.flush()

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer',
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member'])
    def test_manage_external_services(self, app, dbsession, group):
        environ = make_environ(userid=USERID, groups=[group])

        res = app.get(
            self.url,
            extra_environ=environ,
            params={})

        assert 200 == res.status_code

    def test_not_authenticated(self, app):
        res = app.get(self.url, status='*')

        assert res.status_code == 401


class TestExternalServices:

    url = '/studies/test_study/external-services'

    @pytest.fixture(autouse=True)
    def transact(app, dbsession, factories):
        import transaction

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            dbsession.info['blame'] = factories.UserFactory.create(key=USERID)
            dbsession.flush()

            factories.StudyFactory.create(
                name='test_study'
            )

            dbsession.flush()

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer',
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member'])
    def test_external_services(self, app, dbsession, group):
        environ = make_environ(userid=USERID, groups=[group])

        res = app.get(
            self.url,
            extra_environ=environ,
            status='*',
            xhr=True,
            params={})

        assert 200 == res.status_code

    def test_not_authenticated(self, app):
        res = app.get(self.url, status='*', xhr=True)

        assert res.status_code == 401


class TestExternalService:

    url = '/studies/test_study/external-services/test_service'

    @pytest.fixture(autouse=True)
    def transact(app, dbsession, factories):
        import transaction

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            dbsession.info['blame'] = factories.UserFactory.create(key=USERID)
            dbsession.flush()

            study = factories.StudyFactory.build(
                name='test_study'
            )

            factories.ExternalServiceFactory.create(
                name=u'test_service',
                study=study
            )

            dbsession.flush()

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer',
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member'])
    def test_external_services(self, app, dbsession, group):
        environ = make_environ(userid=USERID, groups=[group])

        res = app.get(
            self.url,
            extra_environ=environ,
            status='*',
            xhr=True,
            params={})

        assert 200 == res.status_code

    def test_not_authenticated(self, app):
        res = app.get(self.url, status='*', xhr=True)

        assert res.status_code == 401
