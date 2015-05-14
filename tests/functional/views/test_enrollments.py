from ddt import ddt, data

from tests import FunctionalFixture, USERID


@ddt
class TestPermissionsEnrollmentsListView(FunctionalFixture):

    url = '/studies/patients/123/enrollments'

    def setUp(self):
        super(TestPermissionsEnrollmentsListView, self).setUp()

        import transaction
        from occams import Session
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            Session.info['blame'] = user
            Session.add(user)
            Session.flush()
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
                start_date=date(2014, 12, 12)
            )

            Session.add(studies.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            ))

    @data('administrator', 'manager', 'UCSD:enterer', 'UCSD:reviewer',
          'UCSD:consumer', 'UCSD:member')
    def test_allowed(self, group):
        environ = self.make_environ(userid=USERID, groups=[group])

        response = self.app.get(
            self.url,
            extra_environ=environ,
            status='*',
            xhr=True,
            params={})

        self.assertEquals(200, response.status_code)

    @data('UCLA:enterer', 'UCLA:reviewer',
          'UCLA:consumer', 'UCLA:member')
    def test_not_allowed(self, group):
        environ = self.make_environ(userid=USERID, groups=[group])

        response = self.app.get(
            self.url,
            extra_environ=environ,
            status='*',
            xhr=True,
            params={})

        self.assertEquals(403, response.status_code)

    def test_not_authenticated(self):
        self.app.get(self.url, status=401, xhr=True)


@ddt
class TestPermissionsEnrollmentsAdd(FunctionalFixture):

    url = '/studies/patients/123/enrollments'

    def setUp(self):
        super(TestPermissionsEnrollmentsAdd, self).setUp()

        import transaction
        from occams import Session
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            Session.info['blame'] = user
            Session.add(user)
            Session.flush()
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
                start_date=date(2014, 12, 12)
            )

            Session.add(studies.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            ))

    @data('administrator', 'manager', 'UCSD:enterer')
    def test_allowed(self, group):
        from occams import Session
        from occams_studies import models as studies

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get(self.url, extra_environ=environ, xhr=True)
        study_id = Session.query(studies.Study.id).filter(
            studies.Study.name == u'test_study').scalar()

        data = {
            'consent_date': '2015-01-01',
            'latest_consent_date': '2015-01-01',
            'study': study_id
        }

        csrf_token = self.app.cookies['csrf_token']
        response = self.app.post_json(
            self.url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        self.assertEquals(200, response.status_code)

    @data('UCSD:reviewer', 'UCSD:consumer', 'UCSD:member',
          'UCLA:enterer', None)
    def test_not_allowed(self, group):
        from occams import Session
        from occams_studies import models as studies

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get('/studies', extra_environ=environ, xhr=True)
        study_id = Session.query(studies.Study.id).filter(
            studies.Study.name == u'test_study').scalar()

        data = {
            'consent_date': '2015-01-01',
            'latest_consent_date': '2015-01-01',
            'study': study_id
        }

        csrf_token = self.app.cookies['csrf_token']
        response = self.app.post_json(
            self.url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        self.assertEquals(403, response.status_code)

    def test_not_authenticated(self):
        self.app.get(self.url, status=401, xhr=True)


@ddt
class TestPermissionsEnrollmentView(FunctionalFixture):

    url = '/studies/patients/123/enrollments/{}'

    def setUp(self):
        super(TestPermissionsEnrollmentView, self).setUp()

        import transaction
        from occams import Session
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            Session.info['blame'] = user
            Session.add(user)
            Session.flush()
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
                start_date=date(2014, 12, 12)
            )

            Session.add(studies.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            ))

    @data('administrator', 'manager', 'UCSD:enterer', 'UCSD:reviewer',
          'UCSD:consumer', 'UCSD:member')
    def test_allowed(self, group):
        from occams import Session
        from occams_studies import models as studies

        environ = self.make_environ(userid=USERID, groups=[group])
        enrollment_id = Session.query(studies.Enrollment.id).filter(
            studies.Study.name == u'test_study').scalar()

        data = {
            'id_1': enrollment_id
        }

        response = self.app.get(
            self.url.format(enrollment_id),
            extra_environ=environ,
            status='*',
            xhr=True,
            params=data)

        self.assertEquals(200, response.status_code)

    @data('UCLA:enterer', 'UCLA:reviewer',
          'UCLA:consumer', 'UCLA:member')
    def test_not_allowed(self, group):
        from occams import Session
        from occams_studies import models as studies

        environ = self.make_environ(userid=USERID, groups=[group])
        enrollment_id = Session.query(studies.Enrollment.id).filter(
            studies.Study.name == u'test_study').scalar()

        data = {
            'id_1': enrollment_id
        }

        response = self.app.get(
            self.url.format(enrollment_id),
            extra_environ=environ,
            status='*',
            xhr=True,
            params=data)

        self.assertEquals(403, response.status_code)

    def test_not_authenticated(self):
        from occams import Session
        from occams_studies import models as studies

        enrollment_id = Session.query(studies.Enrollment.id).filter(
            studies.Study.name == u'test_study').scalar()

        self.app.get(self.url.format(enrollment_id), status=401, xhr=True)


@ddt
class TestPermissionsEnrollmentEdit(FunctionalFixture):

    url = '/studies/patients/123/enrollments/{}'

    def setUp(self):
        super(TestPermissionsEnrollmentEdit, self).setUp()

        import transaction
        from occams import Session
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            Session.info['blame'] = user
            Session.add(user)
            Session.flush()
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
                start_date=date(2014, 12, 12)
            )

            Session.add(studies.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            ))

    @data('administrator', 'manager', 'UCSD:enterer')
    def test_allowed(self, group):
        from occams import Session
        from occams_studies import models as studies

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get('/studies/patients/123/enrollments',
                                extra_environ=environ, xhr=True)
        study_id = Session.query(studies.Study.id).filter(
            studies.Study.name == u'test_study').scalar()
        enrollment_id = Session.query(studies.Enrollment.id).filter(
            studies.Study.name == u'test_study').scalar()

        data = {
            'study': study_id,
            'consent_date': '2014-12-22',
            'latest_consent_date': '2015-01-01',
            'reference_number': ''
        }

        csrf_token = self.app.cookies['csrf_token']
        response = self.app.put_json(
            self.url.format(enrollment_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        self.assertEquals(200, response.status_code)

    @data('UCSD:reviewer', 'UCSD:consumer', 'UCSD:member',
          'UCLA:enterer', None)
    def test_not_allowed(self, group):
        from occams import Session
        from occams_studies import models as studies

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get('/studies',
                                extra_environ=environ, xhr=True)
        study_id = Session.query(studies.Study.id).filter(
            studies.Study.name == u'test_study').scalar()
        enrollment_id = Session.query(studies.Enrollment.id).filter(
            studies.Study.name == u'test_study').scalar()

        data = {
            'study': study_id,
            'consent_date': '2014-12-22',
            'latest_consent_date': '2015-01-01',
            'reference_number': ''
        }

        csrf_token = self.app.cookies['csrf_token']
        response = self.app.put_json(
            self.url.format(enrollment_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        self.assertEquals(403, response.status_code)

    def test_not_authenticated(self):
        from occams import Session
        from occams_studies import models as studies

        enrollment_id = Session.query(studies.Enrollment.id).filter(
            studies.Study.name == u'test_study').scalar()

        self.app.get(self.url.format(enrollment_id), status=401, xhr=True)


@ddt
class TestPermissionsEnrollmentDelete(FunctionalFixture):

    url = '/studies/patients/123/enrollments/{}'

    def setUp(self):
        super(TestPermissionsEnrollmentDelete, self).setUp()

        import transaction
        from occams import Session
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            Session.info['blame'] = user
            Session.add(user)
            Session.flush()
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
                start_date=date(2014, 12, 12)
            )

            Session.add(studies.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            ))

    @data('administrator', 'manager')
    def test_allowed(self, group):
        from occams import Session
        from occams_studies import models as studies

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get('/studies/patients/123/enrollments',
                                extra_environ=environ, xhr=True)
        enrollment_id = Session.query(studies.Enrollment.id).filter(
            studies.Study.name == u'test_study').scalar()

        csrf_token = self.app.cookies['csrf_token']
        response = self.app.delete_json(
            self.url.format(enrollment_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params={})

        self.assertEquals(200, response.status_code)

    @data('UCSD:enterer', 'UCSD:reviewer', 'UCSD:consumer',
          'UCSD:member', None)
    def test_not_allowed(self, group):
        from occams import Session
        from occams_studies import models as studies

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get('/studies',
                                extra_environ=environ, xhr=True)
        enrollment_id = Session.query(studies.Enrollment.id).filter(
            studies.Study.name == u'test_study').scalar()

        csrf_token = self.app.cookies['csrf_token']
        response = self.app.delete_json(
            self.url.format(enrollment_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params={})

        self.assertEquals(403, response.status_code)

    def test_not_authenticated(self):
        from occams import Session
        from occams_studies import models as studies

        enrollment_id = Session.query(studies.Enrollment.id).filter(
            studies.Study.name == u'test_study').scalar()

        self.app.get(self.url.format(enrollment_id), status=401, xhr=True)


@ddt
class TestPermissionsEnrollmentTermination(FunctionalFixture):

    url = '/studies/patients/123/enrollments/{}/termination'

    def setUp(self):
        super(TestPermissionsEnrollmentTermination, self).setUp()

        import transaction
        from occams import Session
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            Session.info['blame'] = user
            Session.add(user)
            Session.flush()
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

            form.attributes['termination_date'] = studies.Attribute(
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
                start_date=date(2014, 12, 12),
                termination_schema=form
            )

            Session.add(studies.State(
                name=u'pending-entry',
                title=u'pending-entry'
            ))

            Session.add(studies.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            ))

    @data('administrator', 'manager', 'UCSD:enterer')
    def test_allowed(self, group):
        from occams import Session
        from occams_studies import models as studies

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get('/studies/patients/123',
                                extra_environ=environ)
        enrollment_id = Session.query(studies.Enrollment.id).filter(
            studies.Study.name == u'test_study').scalar()

        data = {
            'ofmetadata_-collect_date': '2015-01-01',
            'ofmetadata_-version': '2015-01-01',
            'ofmetadata_-state': 'pending-entry',
        }

        csrf_token = self.app.cookies['csrf_token']
        response = self.app.post(
            self.url.format(enrollment_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True,
            params=data)

        self.assertEquals(200, response.status_code)

    @data('UCSD:reviewer', 'UCSD:consumer', 'UCSD:member',
          'UCLA:enterer', None)
    def test_not_allowed(self, group):
        from occams import Session
        from occams_studies import models as studies

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get('/studies',
                                extra_environ=environ)
        enrollment_id = Session.query(studies.Enrollment.id).filter(
            studies.Study.name == u'test_study').scalar()

        data = {
            'ofmetadata_-collect_date': '2015-01-01',
            'ofmetadata_-version': '2015-01-01',
            'ofmetadata_-state': 'pending-entry',
        }

        csrf_token = self.app.cookies['csrf_token']
        response = self.app.post(
            self.url.format(enrollment_id),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True,
            params=data)

        self.assertEquals(403, response.status_code)

    def test_not_authenticated(self):
        from occams import Session
        from occams_studies import models as studies

        enrollment_id = Session.query(studies.Enrollment.id).filter(
            studies.Study.name == u'test_study').scalar()

        self.app.get(self.url.format(enrollment_id), status=401, xhr=True)
