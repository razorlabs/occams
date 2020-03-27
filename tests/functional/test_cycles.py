import pytest
from tests.testing import USERID, make_environ, get_csrf_token


class TestPermissionsCyclesAdd:

    url = '/studies/{}/cycles'

    @pytest.fixture(autouse=True)
    def populate(self, request, app, using_dbsession):
        from occams import models
        from datetime import date

        with using_dbsession(app) as dbsession:
            site = models.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            patient = models.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            )

            study = models.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
            )

            dbsession.add(study)
            dbsession.add(patient)

    @pytest.mark.parametrize('group', ['administrator', 'manager'])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        data = {
            'title': 'test_study Week 1',
            'week': '1'
        }

        res = testapp.post_json(
            self.url.format('test_study'),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCSD:enterer', 'UCSD:coordinator', 'UCSD:reviewer',
        'UCSD:consumer', 'UCSD:member', None])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        data = {
            'title': 'test_study Week 1',
            'week': '1'
        }

        res = testapp.post_json(
            self.url.format('test_study'),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated(self, testapp):
        testapp.post(self.url.format('test_study'), status=401, xhr=True)


class TestPermissionsCyclesDelete:

    url = '/studies/test_study/cycles/TestDelete'

    @pytest.fixture(autouse=True)
    def populate(self, app, using_dbsession):
        from occams import models
        from datetime import date

        with using_dbsession(app) as dbsession:
            site = models.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            patient = models.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            )

            study = models.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
            )

            cycle = models.Cycle(
                name=u'TestDelete',
                title=u'TestDelete',
                week=39,
                study=study
            )

            dbsession.add(study)
            dbsession.add(patient)
            dbsession.add(cycle)

    @pytest.mark.parametrize('group', ['administrator', 'manager'])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        res = testapp.delete(
            self.url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True,
            params={})

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCSD:coordinator', 'UCSD:enterer', 'UCSD:reviewer',
        'UCSD:consumer', 'UCSD:member', None])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        res = testapp.delete(
            self.url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True,
            params={})

        assert 403 == res.status_code

    def test_not_authenticated(self, testapp):
        testapp.delete(self.url, status=401, xhr=True)


class TestPermissionsCyclesEdit:

    url = '/studies/test_study/cycles/TestDelete'

    @pytest.fixture(autouse=True)
    def populate(self, app, using_dbsession):
        from occams import models
        from datetime import date

        with using_dbsession(app) as dbsession:
            site = models.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            patient = models.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            )

            study = models.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
            )

            cycle = models.Cycle(
                name=u'TestDelete',
                title=u'TestDelete',
                week=39,
                study=study
            )

            dbsession.add(study)
            dbsession.add(patient)
            dbsession.add(cycle)

    @pytest.mark.parametrize('group', ['administrator', 'manager'])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        data = {
            'name': 'TestDelete',
            'title': 'TestDelete',
            'week': 4
        }

        res = testapp.put_json(
            self.url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCSD:coordinator', 'UCSD:enterer', 'UCSD:reviewer',
        'UCSD:consumer', 'UCSD:member', None])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        data = {
            'name': 'TestDelete',
            'title': 'TestDelete',
            'week': 4
        }

        res = testapp.put_json(
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
        testapp.put(self.url, status=401, xhr=True)


class TestPermissionsCyclesView:

    url = '/studies/test_study/cycles/TestView'

    @pytest.fixture(autouse=True)
    def populate(self, app, using_dbsession):
        from occams import models
        from datetime import date

        with using_dbsession(app) as dbsession:
            site = models.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            patient = models.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            )

            study = models.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
            )

            cycle = models.Cycle(
                name=u'TestView',
                title=u'TestView',
                week=39,
                study=study
            )

            dbsession.add(study)
            dbsession.add(patient)
            dbsession.add(cycle)

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'coordinator', 'enterer',
        'reviewer', 'consumer', 'member'])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        res = testapp.get(
            self.url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True,
            params={})

        assert 200 == res.status_code

    def test_not_authenticated(self, testapp):
        testapp.get(self.url, status=401, xhr=True)
