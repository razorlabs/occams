import pytest
from tests.testing import USERID, make_environ, get_csrf_token


class TestPermissionsStudyList:

    url = '/'

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'enterer', 'reviewer',
        'consumer', 'member', None])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        res = testapp.get(self.url, extra_environ=environ)
        assert 200 == res.status_code

    def test_not_authenticated(self, testapp):
        testapp.get(self.url, status=401)


class TestPermissionsStudyAdd:

    url = '/'

    @pytest.mark.parametrize('group', ['administrator', 'manager'])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        data = {'name': u'test',
                'title': u'test_title',
                'short_title': u'test2',
                'code': u'test3',
                'consent_date': '2015-01-01'}

        res = testapp.post_json(
            self.url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token
            },
            params=data)
        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'enterer', 'reviewer', 'consumer', 'member', None])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        res = testapp.post(
            self.url,
            extra_environ=environ,
            xhr=True,
            status='*')
        assert 403 == res.status_code

    def test_not_authenticated(self, testapp):
        testapp.post(self.url, status=401)


class TestPermissionsStudyView:

    study = 'test'
    url = '/studies/{}'.format(study)

    @pytest.fixture(autouse=True)
    def populate(self, app, using_dbsession):
        import transaction
        from occams import models
        from datetime import date

        with using_dbsession(app) as dbsession:
            dbsession.add(models.Study(
                name=u'test',
                title=u'test',
                short_title=u'test',
                code=u'test',
                consent_date=date.today(),
                is_randomized=False))

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'enterer', 'reviewer',
        'consumer', 'member', None])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        res = testapp.get(self.url, extra_environ=environ)
        assert 200 == res.status_code

    def test_not_authenticated(self, testapp):
        testapp.get(self.url, status=401)


class TestPermissionsStudyEdit:

    study = 'test'
    url = '/studies/{}'.format(study)

    @pytest.fixture(autouse=True)
    def populate(self, app, using_dbsession):
        from occams import models
        from datetime import date

        with using_dbsession(app) as dbsession:
            dbsession.add(
                models.Study(
                    name=u'test',
                    title=u'test',
                    short_title=u'test',
                    code=u'test',
                    consent_date=date.today(),
                    is_randomized=False))

    @pytest.mark.parametrize('group', ['administrator', 'manager'])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        res = testapp.get(self.url, extra_environ=environ, xhr=True)
        data = res.json

        csrf_token = get_csrf_token(testapp, environ)

        res = testapp.put_json(
            self.url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token
            },
            params=data)
        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'enterer', 'reviewer', 'consumer', 'member', None])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        res = testapp.put(
            self.url,
            extra_environ=environ,
            xhr=True,
            status='*')
        assert 403 == res.status_code

    def test_not_authenticated(self, testapp):
        testapp.get(self.url, status=401)


class TestPermissionsStudyDelete:

    study = 'test'
    url = '/studies/{}'.format(study)

    @pytest.fixture(autouse=True)
    def populate(self, app, using_dbsession):
        from occams import models
        from datetime import date

        with using_dbsession(app) as dbsession:
            dbsession.add(
                models.Study(
                    name=u'test',
                    title=u'test',
                    short_title=u'test',
                    code=u'test',
                    consent_date=date.today(),
                    is_randomized=False))

    @pytest.mark.parametrize('group', ['administrator', 'manager'])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        res = testapp.get(self.url, extra_environ=environ, xhr=True)
        data = res.json
        csrf_token = get_csrf_token(testapp, environ)

        res = testapp.delete_json(
            self.url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token
            },
            params=data)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'enterer', 'reviewer', 'consumer', 'member', None])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        res = testapp.get(self.url, extra_environ=environ, xhr=True)
        data = res.json
        csrf_token = get_csrf_token(testapp, environ)

        res = testapp.delete_json(
            self.url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated(self, testapp):
        testapp.delete(self.url, status=401)
