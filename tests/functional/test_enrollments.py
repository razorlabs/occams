import pytest
from tests.testing import USERID, make_environ, get_csrf_token


class TestPermissionsEnrollmentsListView:

    url = '/studies/patients/123/enrollments'

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

            dbsession.add(models.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            ))

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer',
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member'])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])

        res = testapp.get(
            self.url,
            extra_environ=environ,
            status='*',
            xhr=True,
            params={})

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCLA:coordinator', 'UCLA:enterer', 'UCLA:reviewer',
        'UCLA:consumer', 'UCLA:member'])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])

        res = testapp.get(
            self.url,
            extra_environ=environ,
            status='*',
            xhr=True,
            params={})

        assert 403 == res.status_code

    def test_not_authenticated(self, testapp):
        testapp.get(self.url, status=401, xhr=True)


class TestPermissionsEnrollmentsAdd:

    url = '/studies/patients/123/enrollments'

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

            dbsession.add(models.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            ))

            dbsession.flush()
            self.study_id = study.id

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer'])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        data = {
            'consent_date': '2015-01-01',
            'latest_consent_date': '2015-01-01',
            'study': self.study_id
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

        data = {
            'consent_date': '2015-01-01',
            'latest_consent_date': '2015-01-01',
            'study': self.study_id
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
        testapp.get(self.url, status=401, xhr=True)


class TestPermissionsEnrollmentView:

    url = '/studies/patients/123/enrollments/{}'

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

            enrollment = models.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            )

            dbsession.add(enrollment)

            dbsession.flush()
            self.study_id = study.id
            self.enrollment_id = enrollment.id

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer',
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member'])
    def test_allowed(self, testapp, group):

        environ = make_environ(userid=USERID, groups=[group])

        data = {
            'id_1': self.enrollment_id
        }

        res = testapp.get(
            self.url.format(self.enrollment_id),
            extra_environ=environ,
            status='*',
            xhr=True,
            params=data)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCLA:coordinator', 'UCLA:enterer', 'UCLA:reviewer',
        'UCLA:consumer', 'UCLA:member'])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])

        data = {
            'id_1': self.enrollment_id
        }

        res = testapp.get(
            self.url.format(self.enrollment_id),
            extra_environ=environ,
            status='*',
            xhr=True,
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated(self, testapp):
        testapp.get(self.url.format(self.enrollment_id), status=401, xhr=True)


class TestPermissionsEnrollmentEdit:

    url = '/studies/patients/123/enrollments/{}'

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

            enrollment = models.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            )

            dbsession.add(enrollment)
            dbsession.flush()
            self.study_id = study.id
            self.enrollment_id = enrollment.id

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer'])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])

        data = {
            'study': self.study_id,
            'consent_date': '2014-12-22',
            'latest_consent_date': '2015-01-01',
            'reference_number': ''
        }

        csrf_token = get_csrf_token(testapp, environ)
        res = testapp.put_json(
            self.url.format(self.enrollment_id),
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

        data = {
            'study': self.study_id,
            'consent_date': '2014-12-22',
            'latest_consent_date': '2015-01-01',
            'reference_number': ''
        }

        res = testapp.put_json(
            self.url.format(self.enrollment_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated(self, testapp):
        testapp.get(self.url.format(self.enrollment_id), status=401, xhr=True)


class TestPermissionsEnrollmentDelete:

    url = '/studies/patients/123/enrollments/{}'

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

            enrollment = models.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            )
            dbsession.add(enrollment)

            dbsession.flush()
            self.enrollment_id = enrollment.id
            self.study_id = study.id

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator'])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        res = testapp.delete_json(
            self.url.format(self.enrollment_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params={})

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCSD:enterer', 'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member',
        'UCLA:coordinator', None])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        res = testapp.delete_json(
            self.url.format(self.enrollment_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params={})

        assert 403 == res.status_code

    def test_not_authenticated(self, testapp):
        testapp.get(self.url.format(self.enrollment_id), status=401, xhr=True)


class TestPermissionsEnrollmentTermination:

    url = '/studies/patients/123/enrollments/{}/termination'

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

            form.attributes['termination_date'] = models.Attribute(
                name=u'termination_date',
                title=u'termination_date',
                type=u'datetime',
                order=0
            )

            study = models.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
                termination_schema=form
            )

            enrollment = models.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            )
            dbsession.add(enrollment)

            dbsession.flush()
            self.study_id = study.id
            self.enrollment_id = enrollment.id


    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer'])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        data = {
            'ofmetadata_-collect_date': '2015-01-01',
            'ofmetadata_-version': '2015-01-01',
            'ofworkflow_-state': 'pending-review',
        }

        res = testapp.post(
            self.url.format(self.enrollment_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True,
            params=data)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member',
        'UCLA:coordinator', 'UCLA:enterer', None])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(testapp, environ)

        data = {
            'ofmetadata_-collect_date': '2015-01-01',
            'ofmetadata_-version': '2015-01-01',
            'ofmetadata_-state': 'pending-entry',
        }

        res = testapp.post(
            self.url.format(self.enrollment_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True,
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated(self, testapp):
        testapp.get(self.url.format(self.enrollment_id), status=401, xhr=True)


class TestPermissionsEnrollmentRandomization:

    @pytest.fixture(autouse=True)
    def populate(self, app, using_dbsession):
        from datetime import datetime
        import uuid
        from occams import models

        with using_dbsession(app) as dbsession:
            study = models.Study(
                name='teststudy',
                title='Test Study',
                short_title='Test',
                code='000',
                consent_date=datetime.now(),
                is_randomized=True,
                randomization_schema=models.Schema(
                    name='randomization_criteria',
                    title='Randomization Criteria',
                    publish_date=datetime.now(),
                )
            )

            stratum = models.Stratum(
                study=study,
                arm=models.Arm(
                    study=study,
                    name='arm1',
                    title='Arm1',
                ),
                label='control',
                block_number=1,
                randid=str(uuid.uuid4())
            )

            stratum.entities.add(
                models.Entity(
                    schema=study.randomization_schema,
                )
            )

            enrollment = models.Enrollment(
                patient=models.Patient(
                    site=models.Site(
                        name='ucsd',
                        title='UCSD',
                    ),
                    pid=str(uuid.uuid4())
                ),
                consent_date=datetime.now(),
                study=study
            )

            dbsession.add_all([enrollment, stratum])
            dbsession.flush()
            self.patient_pid = enrollment.patient.pid
            self.enrollment_id = enrollment.id

    @pytest.mark.parametrize('group', ['administrator', 'manager'])
    def test_randomize_ajax_allowed(self, testapp, group):
        import uuid

        url = '/studies/patients/{pid}/enrollments/{eid}/randomization'.format(
            pid=self.patient_pid,
            eid=self.enrollment_id,
        )

        environ = make_environ(userid=USERID, groups=[group])

        headers = {
            'X-CSRF-Token': get_csrf_token(testapp, environ),
            'X-REQUESTED-WITH': str('XMLHttpRequest')
        }

        res = testapp.get(
            url,
            extra_environ=environ,
            status='*',
            headers=headers,
            xhr=True,
        )

        assert 302 == res.status_code

        procid = str(uuid.uuid4())

        # CHALLENGE
        res = testapp.post(
            url,
            extra_environ=environ,
            status='*',
            headers=headers,
            xhr=True,
            params={'procid': procid}
        )

        assert 302 == res.status_code

        # ENTRY
        res = testapp.post(
            url,
            extra_environ=environ,
            status='*',
            headers=headers,
            xhr=True,
            params={'procid': procid}
        )

        assert 302 == res.status_code

        # VERIFY
        res = testapp.post(
            url,
            extra_environ=environ,
            status='*',
            headers=headers,
            xhr=True,
            params={'procid': procid}
        )

        assert 302 == res.status_code

    @pytest.mark.parametrize('group', ['UCSD:reviewer', 'UCSD:member', 'None'])
    def test_randomize_ajax_not_allowed(self, testapp, group):
        import uuid

        url = '/studies/patients/{pid}/enrollments/{eid}/randomization'.format(
            pid=self.patient_pid,
            eid=self.enrollment_id
        )

        environ = make_environ(userid=USERID, groups=[group])

        headers = {
            'X-CSRF-Token': get_csrf_token(testapp, environ),
            'X-REQUESTED-WITH': str('XMLHttpRequest')
        }

        res = testapp.get(
            url,
            extra_environ=environ,
            status='*',
            headers=headers,
            xhr=True,
        )

        assert 403 == res.status_code

        procid = str(uuid.uuid4())

        # CHALLENGE
        res = testapp.post(
            url,
            extra_environ=environ,
            status='*',
            headers=headers,
            xhr=True,
            params={'procid': procid}
        )

        assert 403 == res.status_code

        # ENTRY
        res = testapp.post(
            url,
            extra_environ=environ,
            status='*',
            headers=headers,
            xhr=True,
            params={'procid': procid}
        )

        assert 403 == res.status_code

        # VERIFY
        res = testapp.post(
            url,
            extra_environ=environ,
            status='*',
            headers=headers,
            xhr=True,
            params={'procid': procid}
        )

        assert 403 == res.status_code

    def test_not_authenticated(self, testapp):
        import uuid

        url = '/studies/patients/{pid}/enrollments/{eid}/randomization'.format(
            pid=self.patient_pid,
            eid=self.enrollment_id
        )

        res = testapp.get(
            url,
            status='*',
            xhr=True,
        )

        assert 401 == res.status_code

        procid = str(uuid.uuid4())

        # CHALLENGE
        res = testapp.post(
            url,
            status='*',
            xhr=True,
            params={'procid': procid}
        )

        assert 401 == res.status_code

        # ENTRY
        res = testapp.post(
            url,
            status='*',
            xhr=True,
            params={'procid': procid}
        )

        assert 401 == res.status_code

        # VERIFY
        res = testapp.post(
            url,
            status='*',
            xhr=True,
            params={'procid': procid}
        )

        assert 401 == res.status_code
