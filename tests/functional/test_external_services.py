import pytest
from tests.testing import USERID, make_environ

@pytest.fixture(autouse=True)
def populate(app, using_dbsession):
    from datetime import date
    from occams import models

    with using_dbsession(app) as dbsession:
        study = models.Study(
            name=u'test_study',
            code=u'test_code',
            consent_date=date(2014, 12, 23),
            is_randomized=False,
            title=u'test_title',
            short_title=u'test_short',
        )

        external_service = models.ExternalService(
            name='test_service',
            title='Test Service',
            study=study,
            url_template='https://ucsd.edu',
        )

        dbsession.add_all([study, external_service])
        dbsession.flush()


class TestManageExternalServices:

    url = '/studies/test_study/manage-external-services'

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer',
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member'])
    def test_manage_external_services(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])

        res = testapp.get(
            self.url,
            extra_environ=environ,
            params={})

        assert 200 == res.status_code

    def test_not_authenticated(self, testapp):
        res = testapp.get(self.url, status='*')

        assert res.status_code == 401


class TestExternalServices:

    url = '/studies/test_study/external-services'

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer',
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member'])
    def test_external_services(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])

        res = testapp.get(
            self.url,
            extra_environ=environ,
            status='*',
            xhr=True,
            params={})

        assert 200 == res.status_code

    def test_not_authenticated(self, testapp):
        res = testapp.get(self.url, status='*', xhr=True)

        assert res.status_code == 401


class TestExternalService:

    url = '/studies/test_study/external-services/test_service'

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer',
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member'])
    def test_external_services(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])

        res = testapp.get(
            self.url,
            extra_environ=environ,
            status='*',
            xhr=True,
            params={})

        assert 200 == res.status_code

    def test_not_authenticated(self, testapp):
        res = testapp.get(self.url, status='*', xhr=True)

        assert res.status_code == 401
