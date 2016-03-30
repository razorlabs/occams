import pytest
from occams.testing import USERID, make_environ, get_csrf_token


class TestPermissionsEnrollmentsListView:

    url = '/studies/patients/123/enrollments'

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

            db_session.add(studies.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            ))

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:enterer', 'UCSD:reviewer',
        'UCSD:consumer', 'UCSD:member'])
    def test_allowed(self, app, db_session, group):
        environ = make_environ(userid=USERID, groups=[group])

        res = app.get(
            self.url,
            extra_environ=environ,
            status='*',
            xhr=True,
            params={})

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCLA:enterer', 'UCLA:reviewer', 'UCLA:consumer', 'UCLA:member'])
    def test_not_allowed(self, app, db_session, group):
        environ = make_environ(userid=USERID, groups=[group])

        res = app.get(
            self.url,
            extra_environ=environ,
            status='*',
            xhr=True,
            params={})

        assert 403 == res.status_code

    def test_not_authenticated(self, app, db_session):
        app.get(self.url, status=401, xhr=True)


class TestPermissionsEnrollmentsAdd:

    url = '/studies/patients/123/enrollments'

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

            db_session.add(studies.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            ))

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:enterer'])
    def test_allowed(self, app, db_session, group):
        from occams_studies import models as studies

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        study_id = db_session.query(studies.Study.id).filter(
            studies.Study.name == u'test_study').scalar()

        data = {
            'consent_date': '2015-01-01',
            'latest_consent_date': '2015-01-01',
            'study': study_id
        }

        res = app.post_json(
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
    def test_not_allowed(self, app, db_session, group):
        from occams_studies import models as studies

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        study_id = db_session.query(studies.Study.id).filter(
            studies.Study.name == u'test_study').scalar()

        data = {
            'consent_date': '2015-01-01',
            'latest_consent_date': '2015-01-01',
            'study': study_id
        }

        res = app.post_json(
            self.url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated(self, app, db_session):
        app.get(self.url, status=401, xhr=True)


class TestPermissionsEnrollmentView:

    url = '/studies/patients/123/enrollments/{}'

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

            db_session.add(studies.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            ))

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:enterer', 'UCSD:reviewer',
        'UCSD:consumer', 'UCSD:member'])
    def test_allowed(self, app, db_session, group):
        from occams_studies import models as studies

        environ = make_environ(userid=USERID, groups=[group])
        enrollment_id = db_session.query(studies.Enrollment.id).filter(
            studies.Study.name == u'test_study').scalar()

        data = {
            'id_1': enrollment_id
        }

        res = app.get(
            self.url.format(enrollment_id),
            extra_environ=environ,
            status='*',
            xhr=True,
            params=data)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCLA:enterer', 'UCLA:reviewer', 'UCLA:consumer', 'UCLA:member'])
    def test_not_allowed(self, app, db_session, group):
        from occams_studies import models as studies

        environ = make_environ(userid=USERID, groups=[group])
        enrollment_id = db_session.query(studies.Enrollment.id).filter(
            studies.Study.name == u'test_study').scalar()

        data = {
            'id_1': enrollment_id
        }

        res = app.get(
            self.url.format(enrollment_id),
            extra_environ=environ,
            status='*',
            xhr=True,
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated(self, app, db_session):
        from occams_studies import models as studies

        enrollment_id = db_session.query(studies.Enrollment.id).filter(
            studies.Study.name == u'test_study').scalar()

        app.get(self.url.format(enrollment_id), status=401, xhr=True)


class TestPermissionsEnrollmentEdit:

    url = '/studies/patients/123/enrollments/{}'

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

            db_session.add(studies.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            ))

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:enterer'])
    def test_allowed(self, app, db_session, group):
        from occams_studies import models as studies

        environ = make_environ(userid=USERID, groups=[group])
        res = app.get(
            '/studies/patients/123/enrollments',
            extra_environ=environ, xhr=True)
        study_id = db_session.query(studies.Study.id).filter(
            studies.Study.name == u'test_study').scalar()
        enrollment_id = db_session.query(studies.Enrollment.id).filter(
            studies.Study.name == u'test_study').scalar()

        data = {
            'study': study_id,
            'consent_date': '2014-12-22',
            'latest_consent_date': '2015-01-01',
            'reference_number': ''
        }

        csrf_token = app.cookies['csrf_token']
        res = app.put_json(
            self.url.format(enrollment_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member', 'UCLA:enterer', None])
    def test_not_allowed(self, app, db_session, group):
        from occams_studies import models as studies

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        study_id = db_session.query(studies.Study.id).filter(
            studies.Study.name == u'test_study').scalar()
        enrollment_id = db_session.query(studies.Enrollment.id).filter(
            studies.Study.name == u'test_study').scalar()

        data = {
            'study': study_id,
            'consent_date': '2014-12-22',
            'latest_consent_date': '2015-01-01',
            'reference_number': ''
        }

        res = app.put_json(
            self.url.format(enrollment_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated(self, app, db_session):
        from occams_studies import models as studies

        enrollment_id = db_session.query(studies.Enrollment.id).filter(
            studies.Study.name == u'test_study').scalar()

        app.get(self.url.format(enrollment_id), status=401, xhr=True)


class TestPermissionsEnrollmentDelete:

    url = '/studies/patients/123/enrollments/{}'

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

            db_session.add(studies.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            ))

    @pytest.mark.parametrize('group', ['administrator', 'manager'])
    def test_allowed(self, app, db_session, group):
        from occams_studies import models as studies

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        enrollment_id = db_session.query(studies.Enrollment.id).filter(
            studies.Study.name == u'test_study').scalar()

        res = app.delete_json(
            self.url.format(enrollment_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params={})

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCSD:enterer', 'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member', None])
    def test_not_allowed(self, app, db_session, group):
        from occams_studies import models as studies

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        enrollment_id = db_session.query(studies.Enrollment.id).filter(
            studies.Study.name == u'test_study').scalar()

        res = app.delete_json(
            self.url.format(enrollment_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params={})

        assert 403 == res.status_code

    def test_not_authenticated(self, app, db_session):
        from occams_studies import models as studies

        enrollment_id = db_session.query(studies.Enrollment.id).filter(
            studies.Study.name == u'test_study').scalar()

        app.get(self.url.format(enrollment_id), status=401, xhr=True)


class TestPermissionsEnrollmentTermination:

    url = '/studies/patients/123/enrollments/{}/termination'

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

            form = datastore.Schema(
                name=u'test_schema',
                title=u'test_title',
                publish_date=date(2015, 1, 1)
            )

            form.attributes['termination_date'] = datastore.Attribute(
                name=u'termination_date',
                title=u'termination_date',
                type=u'datetime',
                order=0
            )

            study = studies.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
                termination_schema=form
            )

            db_session.add(studies.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            ))

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:enterer'])
    def test_allowed(self, app, db_session, group):
        from occams_studies import models as studies

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        enrollment_id = db_session.query(studies.Enrollment.id).filter(
            studies.Study.name == u'test_study').scalar()

        data = {
            'ofmetadata_-collect_date': '2015-01-01',
            'ofmetadata_-version': '2015-01-01',
            'ofworkflow_-state': 'pending-review',
        }

        res = app.post(
            self.url.format(enrollment_id),
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
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member', 'UCLA:enterer', None])
    def test_not_allowed(self, app, db_session, group):
        from occams_studies import models as studies

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        enrollment_id = db_session.query(studies.Enrollment.id).filter(
            studies.Study.name == u'test_study').scalar()

        data = {
            'ofmetadata_-collect_date': '2015-01-01',
            'ofmetadata_-version': '2015-01-01',
            'ofmetadata_-state': 'pending-entry',
        }

        res = app.post(
            self.url.format(enrollment_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True,
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated(self, app, db_session):
        from occams_studies import models as studies

        enrollment_id = db_session.query(studies.Enrollment.id).filter(
            studies.Study.name == u'test_study').scalar()

        app.get(self.url.format(enrollment_id), status=401, xhr=True)


class TestPermissionsEnrollmentRandomization:

    @pytest.fixture(autouse=True)
    def populate(self, app, db_session, factories):
        import transaction

        with transaction.manager:
            db_session.info['blame'] = factories.UserFactory.create(key=USERID)
            db_session.flush()

            study = factories.StudyFactory.create(
                is_randomized=True,
                randomization_schema=factories.SchemaFactory.create(),
            )

            stratum = factories.StratumFactory.create(study=study)

            stratum.entities.add(
                factories.EntityFactory.create(
                    schema=study.randomization_schema)
            )

            factories.EnrollmentFactory.create(
                patient=factories.PatientFactory.create(),
                study=study
            )

    @pytest.mark.parametrize('group', ['administrator', 'manager'])
    def test_randomize_ajax_allowed(self, app, db_session, factories, group):
        import uuid

        from occams_studies import models as studies

        enrollment = db_session.query(studies.Enrollment).one()

        url = '/studies/patients/{pid}/enrollments/{eid}/randomization'.format(
            pid=enrollment.patient.pid,
            eid=enrollment.id
        )

        environ = make_environ(userid=USERID, groups=[group])

        headers = {
            'X-CSRF-Token': get_csrf_token(app, environ),
            'X-REQUESTED-WITH': str('XMLHttpRequest')
        }

        res = app.get(
            url,
            extra_environ=environ,
            status='*',
            headers=headers,
            xhr=True,
        )

        assert 302 == res.status_code

        procid = str(uuid.uuid4())

        # CHALLENGE
        res = app.post(
            url,
            extra_environ=environ,
            status='*',
            headers=headers,
            xhr=True,
            params={'procid': procid}
        )

        assert 302 == res.status_code

        # ENTRY
        res = app.post(
            url,
            extra_environ=environ,
            status='*',
            headers=headers,
            xhr=True,
            params={'procid': procid}
        )

        assert 302 == res.status_code

        # VERIFY
        res = app.post(
            url,
            extra_environ=environ,
            status='*',
            headers=headers,
            xhr=True,
            params={'procid': procid}
        )

        assert 302 == res.status_code

    @pytest.mark.parametrize('group', ['UCSD:reviewer', 'UCSD:member', 'None'])
    def test_randomize_ajax_not_allowed(self, app, db_session, factories, group):
        import uuid

        from occams_studies import models as studies

        enrollment = db_session.query(studies.Enrollment).one()

        url = '/studies/patients/{pid}/enrollments/{eid}/randomization'.format(
            pid=enrollment.patient.pid,
            eid=enrollment.id
        )

        environ = make_environ(userid=USERID, groups=[group])

        headers = {
            'X-CSRF-Token': get_csrf_token(app, environ),
            'X-REQUESTED-WITH': str('XMLHttpRequest')
        }

        res = app.get(
            url,
            extra_environ=environ,
            status='*',
            headers=headers,
            xhr=True,
        )

        assert 403 == res.status_code

        procid = str(uuid.uuid4())

        # CHALLENGE
        res = app.post(
            url,
            extra_environ=environ,
            status='*',
            headers=headers,
            xhr=True,
            params={'procid': procid}
        )

        assert 403 == res.status_code

        # ENTRY
        res = app.post(
            url,
            extra_environ=environ,
            status='*',
            headers=headers,
            xhr=True,
            params={'procid': procid}
        )

        assert 403 == res.status_code

        # VERIFY
        res = app.post(
            url,
            extra_environ=environ,
            status='*',
            headers=headers,
            xhr=True,
            params={'procid': procid}
        )

        assert 403 == res.status_code

    def test_not_authenticated(self, app, db_session):
        import uuid

        from occams_studies import models as studies

        enrollment = db_session.query(studies.Enrollment).one()

        url = '/studies/patients/{pid}/enrollments/{eid}/randomization'.format(
            pid=enrollment.patient.pid,
            eid=enrollment.id
        )

        res = app.get(
            url,
            status='*',
            xhr=True,
        )

        assert 401 == res.status_code

        procid = str(uuid.uuid4())

        # CHALLENGE
        res = app.post(
            url,
            status='*',
            xhr=True,
            params={'procid': procid}
        )

        assert 401 == res.status_code

        # ENTRY
        res = app.post(
            url,
            status='*',
            xhr=True,
            params={'procid': procid}
        )

        assert 401 == res.status_code

        # VERIFY
        res = app.post(
            url,
            status='*',
            xhr=True,
            params={'procid': procid}
        )

        assert 401 == res.status_code
