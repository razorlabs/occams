import pytest
from tests.testing import USERID, make_environ, get_csrf_token


class TestPermissionsPatientList:

    url = '/studies/patients'

    @pytest.fixture(autouse=True)
    def populate(self, app, using_dbsession):
        from datetime import date
        from occams import models

        with using_dbsession(app) as dbsession:
            dbsession.add(models.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today()))
            dbsession.flush()

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer',
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member'])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        res = testapp.get(self.url, extra_environ=environ)
        assert 200 == res.status_code

    def test_not_authenticated(self, testapp):
        testapp.get(self.url, status=401)


class TestPermissionsPatientAdd:

    url = '/studies/patients'

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
            dbsession.add(site)
            dbsession.flush()
            self.site_id = site.id

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer'])
    def test_allowed(self, testapp, group):
        from occams import models

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        site_id = self.site_id

        data = {
            'site': site_id,
            'references': [],
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
        'UCLA:coordinator', 'UCLA:enterer', None])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        site_id = self.site_id

        data = {
            'site': site_id,
            'references': []
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
        testapp.post(self.url, status=401)


class TestPermissionsPatientView:

    url = '/studies/patients/{}'

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

            dbsession.add(models.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            ))

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer',
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member'])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        res = testapp.get(
            self.url.format('123'), extra_environ=environ, status='*')

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCLA:coordinator', 'UCLA:enterer', 'UCLA:reviewer',
        'UCLA:consumer', 'UCLA:member'])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        res = testapp.get(
            self.url.format('123'), extra_environ=environ, status='*')

        assert 403 == res.status_code

    def test_not_authenticated(self, testapp):
        testapp.get(self.url.format('123'), status=401)


class TestPermissionsPatientDelete:

    url = '/studies/patients/{}'

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
            dbsession.add(patient)
            dbsession.flush()

            # unbind from sesssion so we can use it freely
            dbsession.expunge(patient)
            self.patient = patient


    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator'])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        patient = self.patient

        data = {
            'initials': patient.initials,
            'nurse': patient.nurse,
            'site_id': patient.site_id,
            'pid': patient.pid
        }

        res = testapp.delete_json(
            self.url.format('123'),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCSD:enterer', 'UCSD:reviewer', 'UCSD:consumer',
        'UCSD:member', 'UCLA:coorindator', None])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        patient = self.patient
        data = {
            'initials': patient.initials,
            'nurse': patient.nurse,
            'site_id': patient.site_id,
            'pid': patient.pid
        }

        res = testapp.delete_json(
            self.url.format('123'),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated(self, testapp):
        testapp.delete(self.url.format('123'), status=401, xhr=True)


class TestPermissionsPatientEdit:

    url = '/studies/patients/{}'

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
            dbsession.add(patient)
            dbsession.flush()

            # Unbind from session to use a plain object
            dbsession.expunge(patient)
            self.patient = patient

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer'])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        patient = self.patient
        data = {
            'initials': patient.initials,
            'nurse': patient.nurse,
            'site_id': patient.site_id,
            'pid': patient.pid,
            'site': patient.site_id
        }

        res = testapp.put_json(
            self.url.format('123'),
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
        'UCLA:coorindator', 'UCLA:enterer', None])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        patient = self.patient
        data = {
            'initials': patient.initials,
            'nurse': patient.nurse,
            'site_id': patient.site_id,
            'pid': patient.pid,
            'site': patient.site_id
        }

        res = testapp.put_json(
            self.url.format('123'),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated(self, testapp):
        testapp.put(self.url.format('123'), status=401, xhr=True)


class TestPermissionsPatientViewDiffSite:

    url = '/studies/patients/123'

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

            dbsession.add(models.Site(
                name=u'UCLA',
                title=u'UCLA',
                description=u'UCLA Campus',
                create_date=date.today()))

            dbsession.add(models.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            ))

            dbsession.flush()

    @pytest.mark.parametrize('group', ['UCLA:member'])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        res = testapp.get(
            self.url.format('123'), extra_environ=environ, status='*')

        assert 403 == res.status_code


class TestPermissionsPatientFormsView:

    url = '/studies/patients/123/forms'

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

            dbsession.add(models.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            ))

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer',
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member'])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        res = testapp.get(self.url, extra_environ=environ, status='*')

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCLA:coordinator', 'UCLA:enterer', 'UCLA:reviewer',
        'UCLA:consumer', 'UCLA:member'])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        res = testapp.get(self.url, extra_environ=environ, status='*')

        assert 403 == res.status_code

    def test_not_authenticated(self, testapp):
        testapp.get(self.url.format('123'), status=401)


class TestPermissionsPatientFormsAdd:

    url = '/studies/patients/123/forms'

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

            dbsession.add(models.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            ))
            dbsession.flush()
            self.schema_id = form.id

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer'])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        schema_id = self.schema_id

        data = {
            'collect_date': '2015-01-01',
            'schema': schema_id
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
        'UCLA:coordinator', 'UCLA:enterer', None])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        schema_id = self.schema_id

        data = {
            'collect_date': '2015-01-01',
            'schema': schema_id
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
        testapp.post(self.url.format('123'), status=401)


class TestPermissionsPatientFormsDelete:

    url = '/studies/patients/123/forms'

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

            dbsession.add(models.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            ))

            entity = models.Entity(schema=form)
            dbsession.add(entity)
            dbsession.flush()
            self.entity_id = entity.id

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator'])
    def test_allowed(self, testapp, group):

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        data = {
            'forms': [self.entity_id]
        }

        res = testapp.delete_json(
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
        'UCSD:enterer', 'UCSD:reviewer', 'UCSD:consumer',
        'UCSD:member',
        'UCLA:coordinator', None])
    def test_not_allowed(self, testapp, group):

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        data = {
            'forms': [self.entity_id]
        }

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


class TestPermissionsPatientFormView:

    url = '/studies/patients/123/forms/{}'

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

            state = (
                dbsession.query(models.State)
                .filter_by(name=u'pending-entry')
                .one())

            entity = models.Entity(
                state=state,
                schema=form,
                collect_date=date(2015, 2, 1)
            )
            dbsession.add(entity)
            dbsession.add(models.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            ))
            dbsession.flush()
            self.entity_id = entity.id

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer',
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member'])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        entity_id = self.entity_id
        res = testapp.get(
            self.url.format(entity_id), extra_environ=environ)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCLA:coordinator', 'UCLA:enterer',
        'UCLA:reviewer', 'UCLA:consumer', 'UCLA:member'])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        entity_id = self.entity_id
        res = testapp.get(
            self.url.format(entity_id), extra_environ=environ, status='*')

        assert 403 == res.status_code

    def test_not_authenticated(self, testapp):
        entity_id = self.entity_id
        testapp.get(self.url.format(entity_id), status=401)


class TestPermissionsPatientFormsEdit:

    url = '/studies/patients/123/forms/{}'

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

            state = (
                dbsession.query(models.State)
                .filter_by(name=u'pending-entry')
                .one())

            entity = models.Entity(
                state=state,
                schema=form,
                collect_date=date(2015, 2, 1)
            )
            dbsession.add(entity)

            dbsession.add(models.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            ))
            dbsession.flush()
            self.entity_id = entity.id

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer'])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        entity_id = self.entity_id
        res = testapp.post(
            self.url.format(entity_id), extra_environ=environ,
            params={'id_1': entity_id})

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member',
        'UCLA:coordinator', 'UCLA:enterer', 'UCLA:enterer', None])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        entity_id = self.entity_id
        res = testapp.post(
            self.url.format(entity_id), extra_environ=environ,
            params={'id_1': entity_id}, status='*')

        assert 403 == res.status_code

    def test_not_authenticated(self, testapp):
        entity_id = self.entity_id
        testapp.post(self.url.format(entity_id), status=401)
