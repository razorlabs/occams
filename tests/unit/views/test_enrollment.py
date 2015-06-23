import mock

from tests import IntegrationFixture


def _register_routes(config):
    config.add_route('studies.patient', '/p/{patient}')
    config.add_route('studies.enrollment', '/e/{enrollment}')
    config.add_route('studies.enrollment_randomization', '/e/{enrollment}/rand')
    config.add_route('studies.enrollment_termination', '/e/{enrollment}/term')


class TestViewJson(IntegrationFixture):

    def call_view(self, context, request):
        from occams_studies.views.enrollment import view_json as view
        return view(context, request)

    def test_hide_blinded_randomization(self):
        """
        It should not include randomization status if study is blinded
        """
        from datetime import date
        from pyramid import testing
        from occams_studies import models, Session

        _register_routes(self.config)

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


@mock.patch('occams_studies.views.enrollment.check_csrf_token')
class TestEditJson(IntegrationFixture):

    def call_view(self, context, request):
        from occams_studies.views.enrollment import edit_json as view
        return view(context, request)

    def test_save(self, check_csrf_token):
        from datetime import date
        from pyramid import testing
        from occams_studies import models, Session

        _register_routes(self.config)

        today = date.today()

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=today,
            consent_date=today)

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        Session.add_all([patient, study])
        Session.flush()

        payload = {
            'study': str(study.id),
            'consent_date': str(today),
            'latest_consent_date': str(today),
            'termination_date': str(today),
            'reference_number': u'123'
        }

        response = self.call_view(
            patient['enrollments'], testing.DummyRequest(json_body=payload))

        enrollment = Session.query(models.Enrollment).get(response['id'])

        actual = {
            'study': str(enrollment.study.id),
            'consent_date': str(enrollment.consent_date),
            'latest_consent_date': str(enrollment.latest_consent_date),
            'termination_date': str(enrollment.termination_date),
            'reference_number': str(enrollment.reference_number)
        }

        self.assertEquals(payload, actual)

    def test_unique_consent(self, check_csrf_token):
        """
        It should allow multiple enrollments to a study, but a single consent.
        """
        from datetime import date
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams_studies import models, Session

        _register_routes(self.config)

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

        self.assertIn(
            'This enrollment already exists.',
            cm.exception.json['errors']['consent_date'])

    def test_disable_study_update(self, check_csrf_token):
        """
        It should not allow a enrollment's study to be changed
        """
        from datetime import date
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams_studies import models, Session

        _register_routes(self.config)

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

        self.assertIn(
            'Cannot change an enrollment\'s study.',
            cm.exception.json['errors']['study'])

    def test_timeline_start_date(self, check_csrf_token):
        """
        It should not allow consent dates before the study start date
        """
        from datetime import date, timedelta
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams_studies import models, Session

        _register_routes(self.config)

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
                    'consent_date': str(invalid_date),
                    'latest_consent_date': str(invalid_date),
                    }
                ))

        self.assertIn(
            'Cannot enroll before the study start date',
            cm.exception.json['errors']['latest_consent_date'])

    def test_timeline_end_date(self, check_csrf_token):
        """
        It should not allow consent dates after the study end date
        """
        from datetime import date, timedelta
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams_studies import models, Session

        _register_routes(self.config)

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
            end_date=t3,
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
                    'consent_date': str(invalid_date),
                    'latest_consent_date': str(invalid_date),
                    }
                ))

        self.assertIn(
            'Cannot enroll after the study end date',
            cm.exception.json['errors']['latest_consent_date'])

    def test_update_patient(self, check_csrf_token):
        """
        It should mark the patient as updated
        """
        from datetime import date
        from pyramid import testing
        from occams_studies import models, Session

        _register_routes(self.config)

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

        old_modify_date = patient.modify_date
        self.call_view(patient['enrollments'], testing.DummyRequest(
            json_body={
                'study': study.id,
                'consent_date': str(date.today()),
                'latest_consent_date': str(date.today())
                }))
        self.assertLess(old_modify_date, patient.modify_date)

    def test_temination_date_disabled_if_form_configured(self, csrf_token):

        from datetime import date, timedelta
        from pyramid import testing
        from occams_studies import models, Session

        _register_routes(self.config)

        today = date.today()
        t1 = today - timedelta(days=5)
        t2 = today
        t3 = today + timedelta(days=100)
        t4 = today + timedelta(days=200)

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=t1,
            consent_date=t3,
            termination_schema=models.Schema(
                name=u'termination',
                title=u'Termination',
                publish_date=t1,
                attributes={
                    'termination_date': models.Attribute(
                        name=u'termination_date',
                        title=u'Termination Date',
                        type=u'date',
                        order=0)
                }))

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        enrollment = models.Enrollment(
            study=study,
            patient=patient,
            consent_date=t1,
            termination_date=t3)

        Session.add_all([enrollment])
        Session.flush()

        self.call_view(enrollment, testing.DummyRequest(
            json_body={
                'study': study.id,
                'consent_date': str(t1),
                'latest_consent_date': str(t2),
                'termination_date': str(t4)
                }
            ))

        # Termination date should not have changed because
        # it's controlled via termination schema
        self.assertEquals(t3, enrollment.termination_date)

    def test_temination_date_enabled_if_no_termination(self, csrf_token):

        from datetime import date, timedelta
        from pyramid import testing
        from occams_studies import models, Session

        _register_routes(self.config)

        today = date.today()
        t1 = today - timedelta(days=5)
        t2 = today
        t3 = today + timedelta(days=100)
        t4 = today + timedelta(days=200)

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=t1,
            consent_date=t3)

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        enrollment = models.Enrollment(
            study=study,
            patient=patient,
            consent_date=t1,
            termination_date=t3)

        Session.add_all([enrollment])
        Session.flush()

        self.call_view(enrollment, testing.DummyRequest(
            json_body={
                'study': study.id,
                'consent_date': str(t1),
                'latest_consent_date': str(t2),
                'termination_date': str(t4)
                }
            ))

        # Termination date should have changed because there
        # is not termination schema that controls it
        self.assertEquals(t4, enrollment.termination_date)


@mock.patch('occams_studies.views.enrollment.check_csrf_token')
class TestDeleteJson(IntegrationFixture):

    def call_view(self, context, request):
        from occams_studies.views.enrollment import delete_json as view
        return view(context, request)

    def test_update_patient(self, check_csrf_token):
        """
        It should mark the patient as updated
        """
        from datetime import date
        from pyramid import testing
        from occams_studies import models, Session

        _register_routes(self.config)

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

        Session.add_all([patient, enrollment, study])
        Session.flush()

        old_modify_date = patient.modify_date
        self.call_view(enrollment, testing.DummyRequest())
        self.assertLess(old_modify_date, patient.modify_date)

    def test_cascade_forms(self, check_csrf_token):
        """
        It should also remove termination forms.
        """
        from datetime import date
        from pyramid import testing
        from occams_studies import models, Session

        _register_routes(self.config)

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
