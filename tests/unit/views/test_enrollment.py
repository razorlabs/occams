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

        self.assertEqual(
            'Reference number already in use.',
            cm.exception.json['validation_errors'][0])
