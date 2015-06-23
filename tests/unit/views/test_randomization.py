from tests import IntegrationFixture

import mock


def _register_routes(config):
    config.add_route('studies.patient', '/p/{patient}')
    config.add_route('studies.enrollment', '/e/{enrollment}')
    config.add_route('studies.enrollment_randomization', '/e/{enrollment}/rand')
    config.add_route('studies.enrollment_termination', '/e/{enrollment}/term')


class TestRandomization(IntegrationFixture):

    def setUp(self):
        super(TestRandomization, self).setUp()

        from datetime import date

        from occams import Session
        from occams_studies import models

        _register_routes(self.config)

        self.schema = models.Schema(
            name=u'criteria', title=u'Criteria', publish_date=date.today())

        self.study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'study',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today(),
            randomization_schema=self.schema,
            is_randomized=True)

        self.stratum = models.Stratum(
            randid=u'98765',
            block_number='111',
            study=self.study,
            arm=models.Arm(
                name=u'tested',
                title=u'Tested',
                study=self.study))

        self.stratum2 = models.Stratum(
            randid=u'98766',
            block_number='111',
            study=self.study,
            arm=models.Arm(
                name=u'tested2',
                title=u'Tested2',
                study=self.study))

        self.stratum.entities.add(models.Entity(schema=self.schema))
        self.stratum2.entities.add(models.Entity(schema=self.schema))

        self.site = models.Site(name=u'ucsd', title=u'UCSD')

        self.enrollment = models.Enrollment(
            patient=models.Patient(
                site=self.site,
                pid=u'12345'),
            study=self.study,
            consent_date=date.today())

        self.enrollment2 = models.Enrollment(
            patient=models.Patient(
                site=self.site,
                pid=u'12346'),
            study=self.study,
            consent_date=date.today())

        Session.add_all(
            [self.study, self.stratum, self.stratum2, self.enrollment, self.enrollment2])
        Session.flush()

    def call_view(self, context, request):
        from occams_studies.views.enrollment import randomize_ajax as view
        return view(context, request)

    def test_challenge(self):
        from pyramid import testing

        self.config.include('pyramid_chameleon')
        request = testing.DummyRequest()
        request.session = {}

        enrollment = self.enrollment

        self.call_view(enrollment, request)

        self.assertEquals(request.session['randomization_stage'], 0)

    @mock.patch('occams_studies.views.enrollment.check_csrf_token')
    def test_transition_from_enter_to_verify(self, check_csrf_token):
        from pyramid import testing

        from webob.multidict import MultiDict

        self.config.include('pyramid_chameleon')
        payload = MultiDict()
        request = testing.DummyRequest(
            post=payload,
            matchdict={'enrollment': self.enrollment})

        enrollment = self.enrollment

        request.session['randomization_stage'] = 1

        self.call_view(enrollment, request)

        self.assertEquals(request.session['randomization_stage'], 2)

    @mock.patch('occams_studies.views.enrollment.check_csrf_token')
    def test_transition_from_verify_to_complete(self, check_csrf_token):
        from pyramid import testing

        from webob.multidict import MultiDict

        self.config.include('pyramid_chameleon')
        payload = MultiDict()
        request = testing.DummyRequest(
            post=payload,
            matchdict={'enrollment': self.enrollment})

        enrollment = self.enrollment

        request.session['randomization_stage'] = 2

        self.call_view(enrollment, request)

        self.assertEquals(request.session['randomization_stage'], 3)
