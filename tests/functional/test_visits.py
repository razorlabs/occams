import pytest
from tests.testing import USERID, make_environ, get_csrf_token

class TestPermissionsVisitsView:

    url = '/studies/patients/123/visits'

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

            dbsession.add(study)
            dbsession.add(patient)

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:enterer',
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member'])
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

    @pytest.mark.parametrize('group', [
        'UCLA:enterer', 'UCLA:reviewer',
        'UCLA:consumer', 'UCLA:member'])
    def test_not_allowed(self, testapp, group):
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

        assert 403 == res.status_code

    def test_not_authenticated(self, testapp):
        testapp.get(self.url, status=401, xhr=True)


class TestPermissionsVisitsAdd:

    url = '/studies/patients/123/visits'

    @pytest.fixture(autouse=True)
    def populate(self, app,using_dbsession):
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
                name=u'TestCycle',
                title=u'TestCycle',
                week=39,
                study=study
            )

            dbsession.add(study)
            dbsession.add(patient)
            dbsession.add(cycle)
            dbsession.flush()

            dbsession.expunge_all()
            self.study = study
            self.patient = patient
            self.cycle = cycle

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:enterer'])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        cycle_id = self.cycle.id
        data = {
            'cycles': [cycle_id],
            'visit_date': '2015-01-01',
            'include_forms': False,
            'include_speciman': False
        }

        res = testapp.post_json(
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
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member',
        'UCLA:enterer', None])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        cycle_id = self.cycle.id

        data = {
            'cycles': [cycle_id],
            'visit_date': '2015-01-01',
            'include_forms': False,
            'include_speciman': False
        }

        res = testapp.post_json(
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
        testapp.post(self.url, status=401, xhr=True)


class TestPermissionsVisitView:

    url = '/studies/patients/123/visits/{}'

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
                name=u'TestCycle',
                title=u'TestCycle',
                week=39,
                study=study
            )

            visit = models.Visit(
                patient=patient,
                cycles=[cycle],
                visit_date='2015-01-01'
            )

            dbsession.add(study)
            dbsession.add(patient)
            dbsession.add(visit)
            dbsession.flush()

            dbsession.expunge_all()
            self.study = study
            self.patient = patient
            self.visit = visit

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:enterer', 'UCSD:reviewer',
        'UCSD:consumer', 'UCSD:member'])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        visit_date = self.visit.visit_date

        res = testapp.get(
            self.url.format(visit_date),
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
        'UCLA:enterer', 'UCLA:reviewer',
        'UCLA:consumer', 'UCLA:member'])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        visit_date = self.visit.visit_date

        res = testapp.get(
            self.url.format(visit_date),
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
        visit_date = self.visit.visit_date
        testapp.get(self.url.format(visit_date), status=401, xhr=True)


class TestPermissionsVisitDelete:

    url = '/studies/patients/123/visits/{}'

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
                name=u'TestCycle',
                title=u'TestCycle',
                week=39,
                study=study
            )

            visit = models.Visit(
                patient=patient,
                cycles=[cycle],
                visit_date='2015-01-01'
            )

            dbsession.add(study)
            dbsession.add(patient)
            dbsession.add(visit)
            dbsession.flush()

            dbsession.expunge_all()
            self.study = study
            self.patient = patient
            self.visit = visit

    @pytest.mark.parametrize('group', ['administrator', 'manager'])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        visit_date = self.visit.visit_date

        res = testapp.delete(
            self.url.format(visit_date),
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
        'UCSD:enterer', 'UCSD:reviewer',
        'UCSD:consumer', 'UCSD:member', None])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        visit_date = self.visit.visit_date

        res = testapp.delete(
            self.url.format(visit_date),
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
        visit_date = self.visit.visit_date
        testapp.delete(self.url.format(visit_date), status=401, xhr=True)


class TestPermissionsVisitEdit:

    url = '/studies/patients/123/visits/{}'

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
                name=u'TestCycle',
                title=u'TestCycle',
                week=39,
                study=study
            )

            visit = models.Visit(
                patient=patient,
                cycles=[cycle],
                visit_date='2015-01-01'
            )

            dbsession.add(study)
            dbsession.add(patient)
            dbsession.add(visit)
            dbsession.flush()

            dbsession.expunge_all()
            self.study = study
            self.cycle = cycle
            self.patient = patient
            self.visit = visit

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:enterer'])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        visit_date = self.visit.visit_date
        cycle_id = self.cycle.id

        data = {
            'cycles': [cycle_id],
            'visit_date': '2015-01-02'
        }

        res = testapp.put_json(
            self.url.format(visit_date),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member',
        'UCLA:enterer', None])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        visit_date = self.visit.visit_date
        cycle_id = self.cycle.id

        data = {
            'cycles': [cycle_id],
            'visit_date': '2015-01-02'
        }

        res = testapp.put_json(
            self.url.format(visit_date),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated(self, testapp):
        visit_date = self.visit.visit_date
        testapp.put(self.url.format(visit_date), status=401, xhr=True)


class TestPermissionsVisitFormsAdd:

    url = '/studies/patients/123/visits/2015-01-01/forms'

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

            form = models.Schema(
                name=u'test_schema',
                title=u'test_title',
                publish_date=date(2015, 1, 1)
            )

            study = models.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
                schemata=set([form])
            )

            cycle = models.Cycle(
                name=u'TestCycle',
                title=u'TestCycle',
                week=39,
                study=study
            )

            visit = models.Visit(
                patient=patient,
                cycles=[cycle],
                visit_date='2015-01-01'
            )

            dbsession.add(study)
            dbsession.add(patient)
            dbsession.add(visit)
            dbsession.flush()

            dbsession.expunge_all()
            self.study = study
            self.cycle = cycle
            self.patient = patient
            self.visit = visit
            self.form = form

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:enterer'])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        form_id = self.form.id

        data = {
            'schema': form_id,
            'collect_date': '2015-01-01'
        }

        res = testapp.post_json(
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
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member',
        'UCLA:enterer', None])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        form_id = self.form.id

        data = {
            'schema': form_id,
            'collect_date': '2015-01-01'
        }

        res = testapp.post_json(
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
        testapp.post(self.url, status=401, xhr=True)


class TestPermissionsVisitFormsDelete:

    url = '/studies/patients/123/visits/2015-01-01/forms'

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

            form = models.Schema(
                name=u'test_schema',
                title=u'test_title',
                publish_date=date(2015, 1, 1)
            )

            study = models.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
                schemata=set([form])
            )

            cycle = models.Cycle(
                name=u'TestCycle',
                title=u'TestCycle',
                week=39,
                study=study
            )

            visit = models.Visit(
                patient=patient,
                cycles=[cycle],
                visit_date='2015-01-01'
            )

            entity = models.Entity(
                schema=form,
                collect_date=date(2015, 1, 1)
            )

            dbsession.add(study)
            dbsession.add(patient)
            dbsession.add(visit)
            dbsession.add(entity)
            patient.entities.add(entity)
            dbsession.flush()

            dbsession.expunge_all()
            self.study = study
            self.cycle = cycle
            self.form = form
            self.patient = patient
            self.visit = visit
            self.entity = entity

    @pytest.mark.parametrize('group', ['administrator', 'manager'])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        form_id = self.form.id
        entity_id = self.entity.id

        res = testapp.delete_json(
            self.url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params={'forms': [entity_id]})

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCSD:enterer', 'UCSD:reviewer', 'UCSD:consumer',
        'UCSD:member', None])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        res = testapp.delete_json(
            self.url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params={})

        assert 403 == res.status_code

    def test_not_authenticated(self, testapp):
        testapp.delete(self.url, status=401, xhr=True)


class TestPermissionsVisitFormView:

    url = '/studies/patients/123/visits/2015-01-01/forms/{}'

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

            form = models.Schema(
                name=u'test_schema',
                title=u'test_title',
                publish_date=date(2015, 1, 1)
            )

            study = models.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
                schemata=set([form])
            )

            cycle = models.Cycle(
                name=u'TestCycle',
                title=u'TestCycle',
                week=39,
                study=study
            )

            visit = models.Visit(
                patient=patient,
                cycles=[cycle],
                visit_date='2015-01-01'
            )

            entity = models.Entity(
                schema=form,
                collect_date=date(2015, 1, 1)
            )

            dbsession.add(study)
            dbsession.add(patient)
            dbsession.add(visit)
            dbsession.add(entity)
            patient.entities.add(entity)
            dbsession.flush()

            dbsession.expunge_all()
            self.study = study
            self.patient = patient
            self.visit = visit
            self.form = form
            self.entity = entity


    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:enterer', 'UCSD:reviewer',
        'UCSD:consumer', 'UCSD:member'])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])

        form_id = self.form.id
        entity_id = self.entity.id

        res = testapp.get(
            self.url.format(entity_id), extra_environ=environ)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCLA:enterer', 'UCLA:reviewer',
        'UCLA:consumer', 'UCLA:member'])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])

        form_id = self.form.id
        entity_id = self.entity.id

        res = testapp.get(
            self.url.format(entity_id), extra_environ=environ, status='*')

        assert 403 == res.status_code

    def test_not_authenticated(self, testapp):
        form_id = self.form.id
        entity_id = self.entity.id

        testapp.get(self.url.format(entity_id), status=401)


class TestPermissionsVisitFormEdit:

    url = '/studies/patients/123/visits/2015-01-01/forms/{}'

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

            form = models.Schema(
                name=u'test_schema',
                title=u'test_title',
                publish_date=date(2015, 1, 1)
            )

            study = models.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
                schemata=set([form])
            )

            cycle = models.Cycle(
                name=u'TestCycle',
                title=u'TestCycle',
                week=39,
                study=study
            )

            visit = models.Visit(
                patient=patient,
                cycles=[cycle],
                visit_date='2015-01-01'
            )

            entity = models.Entity(
                schema=form,
                collect_date=date(2015, 1, 1)
            )

            dbsession.add(study)
            dbsession.add(patient)
            dbsession.add(visit)
            dbsession.add(entity)
            patient.entities.add(entity)
            dbsession.flush()

            dbsession.expunge_all()
            self.study = study
            self.patient = patient
            self.visit = visit
            self.form = form
            self.entity = entity

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:enterer'])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])

        form_id = self.form.id
        entity_id = self.entity.id

        res = testapp.post(
            self.url.format(entity_id), extra_environ=environ)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member',
        'UCLA:enterer', None])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])

        form_id = self.form.id
        entity_id = self.entity.id

        res = testapp.post(
            self.url.format(entity_id), extra_environ=environ, status='*')

        assert 403 == res.status_code

    def test_not_authenticated(self, testapp):
        form_id = self.form.id
        entity_id = self.entity.id

        testapp.post(self.url.format(entity_id), status=401)
