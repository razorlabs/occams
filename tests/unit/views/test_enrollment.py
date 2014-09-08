import mock

from tests import IntegrationFixture


class TestViewJson(IntegrationFixture):

    def call_view(self, context, request):
        from occams.studies.views.enrollment import view_json as view
        return view(context, request)

    def test_hide_blinded_randomization(self):
        """
        It should not include randomization status if study is blinded
        """
        from datetime import date
        from pyramid import testing
        from occams.studies import models, Session

        self.config.add_route('enrollment', '/{patient}/{enrollment}')

        schema = models.Schema(name=u'criteria', title=u'Criteria')

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today(),
            randomization_schema=schema,
            is_randomized=True)

        enrollment = models.Enrollment(
            patient=models.Patient(
                site=models.Site(name=u'ucsd', title=u'UCSD'),
                pid=u'12345'),
            study=study,
            consent_date=date.today(),
            stratum=models.Stratum(
                randid=u'98765',
                block_number='111',
                study=study,
                arm=models.Arm(
                    name=u'tested',
                    title=u'Tested',
                    study=study)))

        Session.add(enrollment)
        Session.flush()

        study.is_blinded = False
        Session.flush()
        request = testing.DummyRequest()
        response = self.call_view(enrollment, request)
        self.assertIsNotNone(response['stratum']['arm'])

        study.is_blinded = True
        Session.flush()
        request = testing.DummyRequest()
        response = self.call_view(enrollment, request)
        self.assertIsNone(response['stratum']['arm'])


@mock.patch('occams.studies.views.enrollment.check_csrf_token')
class TestEditJson(IntegrationFixture):

    def call_view(self, context, request):
        from occams.studies.views.enrollment import edit_json as view
        return view(context, request)

    def test_unique_consent(self, check_csrf_token):
        """
        It should allow multiple enrollments to a study, but a single consent.
        """
        from datetime import date
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams.studies import models, Session

        self.config.add_route('enrollment', '/{patient}/{enrollment}')

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today())

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        Session.add_all([patient, study])
        Session.flush()

        consent_date = date.today()

        def make_request():
            self.call_view(patient['enrollments'], testing.DummyRequest(
                json_body={
                    'study': str(study.id),
                    'consent_date': str(consent_date),
                    'latest_consent_date': str(consent_date),
                    }
                ))

        make_request()

        self.assertIsNotNone(
            Session.query(models.Enrollment)
            .filter_by(patient=patient, study=study).one())

        # Try adding it again, it should fail
        with self.assertRaises(HTTPBadRequest) as cm:
            make_request()

        self.assertHasStringLike(
            cm.exception.json['validation_errors'],
            'This enrollment already exists.')

    def test_disable_study_update(self, check_csrf_token):
        """
        It should not allow a enrollment's study to be changed
        """
        from datetime import date
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams.studies import models, Session

        self.config.add_route('enrollment', '/{patient}/{enrollment}')

        study1 = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today())

        study2 = models.Study(
            name=u'otherstudy',
            title=u'Other Study',
            short_title=u'ostudy',
            code=u'111',
            start_date=date.today(),
            consent_date=date.today())

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        enrollment = models.Enrollment(
            study=study1,
            patient=patient,
            consent_date=date.today())

        Session.add_all([patient, enrollment, study1, study2])
        Session.flush()

        consent_date = date.today()

        with self.assertRaises(HTTPBadRequest) as cm:
            self.call_view(enrollment, testing.DummyRequest(
                json_body={
                    'study': str(study2.id),
                    'consent_date': str(consent_date),
                    'latest_consent_date': str(consent_date),
                    }
                ))

        self.assertHasStringLike(
            cm.exception.json['validation_errors'],
            'Cannot change an enrollment\'s study.')

    def test_timeline_start_date(self, check_csrf_token):
        """
        It should not allow consent dates before the study start date
        """
        from datetime import date, timedelta
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams.studies import models, Session

        self.config.add_route('enrollment', '/{patient}/{enrollment}')

        today = date.today()
        invalid_date = today - timedelta(days=100)
        t1 = today - timedelta(days=5)
        t2 = today

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=t1,
            consent_date=t2)

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        Session.add_all([patient, study])
        Session.flush()

        with self.assertRaises(HTTPBadRequest) as cm:
            self.call_view(patient['enrollments'], testing.DummyRequest(
                json_body={
                    'study': str(study.id),
                    'consent_date': invalid_date,
                    'latest_consent_date': invalid_date,
                    }
                ))

        self.assertHasStringLike(
            cm.exception.json['validation_errors'],
            'Cannot enroll before the study start date')

    def test_timeline_stop_date(self, check_csrf_token):
        """
        It should not allow consent dates after the study stop date
        """
        from datetime import date, timedelta
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams.studies import models, Session

        self.config.add_route('enrollment', '/{patient}/{enrollment}')

        today = date.today()
        t1 = today - timedelta(days=5)
        t2 = today
        t3 = today + timedelta(days=100)
        invalid_date = today + timedelta(days=200)

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=t1,
            stop_date=t3,
            consent_date=t2)

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        Session.add_all([patient, study])
        Session.flush()

        with self.assertRaises(HTTPBadRequest) as cm:
            self.call_view(patient['enrollments'], testing.DummyRequest(
                json_body={
                    'study': str(study.id),
                    'consent_date': invalid_date,
                    'latest_consent_date': invalid_date,
                    }
                ))

        self.assertHasStringLike(
            cm.exception.json['validation_errors'],
            'Cannot enroll after the study stop date')


@mock.patch('occams.studies.views.enrollment.check_csrf_token')
class TestDeleteJson(IntegrationFixture):

    def call_view(self, context, request):
        from occams.studies.views.enrollment import delete_json as view
        return view(context, request)

    def test_cascade_forms(self, check_csrf_token):
        """
        It should also remove termination forms.
        """
        from datetime import date
        from pyramid import testing
        from occams.studies import models, Session

        self.config.add_route('patient', '/{patient}')

        schema = models.Schema(
            name=u'termination',
            title=u'Termination',
            publish_date=date.today())

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today())

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        enrollment = models.Enrollment(
            study=study,
            patient=patient,
            consent_date=date.today())

        enrollment.entities.add(models.Entity(
            schema=schema,
            collect_date=date.today()))

        Session.add_all([patient, enrollment, study])
        Session.flush()

        enrollment_id = enrollment.id

        self.call_view(enrollment, testing.DummyRequest())

        self.assertIsNone(Session.query(models.Enrollment).get(enrollment_id))
        self.assertEquals(0, Session.query(models.Entity).count())
