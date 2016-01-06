import pytest
from occams.testing import USERID, make_environ, get_csrf_token


class TestPermissionsCyclesAdd:

    url = '/studies/{}/cycles'

    @pytest.fixture(autouse=True)
    def populate(self, app, db_session):

        import transaction
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            db_session.info['blame'] = user
            db_session.add(user)
            db_session.flush()

            site = studies.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            patient = studies.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            )

            study = studies.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
            )

            db_session.add(study)
            db_session.add(patient)

    @pytest.mark.parametrize('group', ['administrator', 'manager'])
    def test_allowed(self, app, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        data = {
            'title': 'test_study Week 1',
            'week': '1'
        }

        res = app.post_json(
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
        'UCSD:enterer', 'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member', None])
    def test_not_allowed(self, app, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        data = {
            'title': 'test_study Week 1',
            'week': '1'
        }

        res = app.post_json(
            self.url.format('test_study'),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated(self, app):
        app.post(self.url.format('test_study'), status=401, xhr=True)


class TestPermissionsCyclesDelete:

    url = '/studies/test_study/cycles/TestDelete'

    @pytest.fixture(autouse=True)
    def populate(self, app, db_session):

        import transaction
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            db_session.info['blame'] = user
            db_session.add(user)
            db_session.flush()

            site = studies.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            patient = studies.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            )

            study = studies.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
            )

            cycle = studies.Cycle(
                name=u'TestDelete',
                title=u'TestDelete',
                week=39,
                study=study
            )

            db_session.add(study)
            db_session.add(patient)
            db_session.add(cycle)

    @pytest.mark.parametrize('group', ['administrator', 'manager'])
    def test_allowed(self, app, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        res = app.delete(
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
        'UCSD:enterer', 'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member', None])
    def test_not_allowed(self, app, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        res = app.delete(
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

    def test_not_authenticated(self, app):
        app.delete(self.url, status=401, xhr=True)


class TestPermissionsCyclesEdit:

    url = '/studies/test_study/cycles/TestDelete'

    @pytest.fixture(autouse=True)
    def populate(self, app, db_session):

        import transaction
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            db_session.info['blame'] = user
            db_session.add(user)
            db_session.flush()

            site = studies.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            patient = studies.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            )

            study = studies.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
            )

            cycle = studies.Cycle(
                name=u'TestDelete',
                title=u'TestDelete',
                week=39,
                study=study
            )

            db_session.add(study)
            db_session.add(patient)
            db_session.add(cycle)

    @pytest.mark.parametrize('group', ['administrator', 'manager'])
    def test_allowed(self, app, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        data = {
            'name': 'TestDelete',
            'title': 'TestDelete',
            'week': 4
        }

        res = app.put_json(
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
        'UCSD:enterer', 'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member', None])
    def test_not_allowed(self, app, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        data = {
            'name': 'TestDelete',
            'title': 'TestDelete',
            'week': 4
        }

        res = app.put_json(
            self.url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated(self, app):
        app.put(self.url, status=401, xhr=True)


class TestPermissionsCyclesView:

    url = '/studies/test_study/cycles/TestView'

    @pytest.fixture(autouse=True)
    def populate(self, app, db_session):

        import transaction
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            db_session.info['blame'] = user
            db_session.add(user)
            db_session.flush()

            site = studies.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            patient = studies.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            )

            study = studies.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
            )

            cycle = studies.Cycle(
                name=u'TestView',
                title=u'TestView',
                week=39,
                study=study
            )

            db_session.add(study)
            db_session.add(patient)
            db_session.add(cycle)

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'enterer', 'reviewer',
        'consumer', 'member'])
    def test_allowed(self, app, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        res = app.get(
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

    def test_not_authenticated(self, app):
        app.get(self.url, status=401, xhr=True)
