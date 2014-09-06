import mock

from tests import IntegrationFixture


@mock.patch('occams.studies.views.visit.check_csrf_token')
class TestEditJson(IntegrationFixture):

    def call_view(self, context, request):
        from occams.studies.views.visit import edit_json as view
        return view(context, request)

    def test_unique_cycle(self, check_csrf_token):
        """
        It should not allow repeat cycles (unless it's interim)
        """
        from datetime import date, timedelta
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams.studies import models, Session

        self.config.add_route('patient', '/{patient}')
        self.config.add_route('visit', '/{patient}/{visit}')

        Session.add(models.State(name='pending-entry', title=u''))

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today())

        cycle = models.Cycle(name='week-1', title=u'', week=1)

        study.cycles.append(cycle)

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        visit = models.Visit(
            patient=patient, cycles=[cycle], visit_date=date.today())

        Session.add_all([patient, study, visit])
        Session.flush()

        def make_request():
            return self.call_view(patient['visits'], testing.DummyRequest(
                json_body={
                    'cycles': [cycle.id],
                    'visit_date': date.today() + timedelta(days=1)}
                ))

        with self.assertRaises(HTTPBadRequest) as cm:
            make_request()

        errors = cm.exception.json['validation_errors']
        expected = 'is already used by visit'
        assert [m for m in errors if expected in m], \
            '"%s" is not in %s' % (expected, errors)

        # The exception is interims
        cycle.is_interim = True
        Session.flush()
        response = make_request()
        self.assertIsNotNone(response)
