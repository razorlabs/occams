import mock

from tests import IntegrationFixture


@mock.patch('occams.studies.views.cycle.check_csrf_token')
class TestEditJson(IntegrationFixture):

    def call_view(self, context, request):
        from occams.studies.views.cycle import edit_json as view
        return view(context, request)

    def test_add(self, check_csrf_token):
        """
        It should be able to add a new cycle
        """
        from datetime import date
        from pyramid import testing
        from occams.studies import Session, models

        self.config.add_route('cycle', '/{study}/{cycle}')

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today())

        Session.add_all([study])
        Session.flush()

        self.call_view(study['cycles'], testing.DummyRequest(
            json_body={
                'name': 'week-1',
                'title': u'Week 1',
                'week': 1}))

        self.assertEqual(1, study.cycles.count())
        self.assertEqual('week-1', study.cycles[0].name)

    def test_enforce_unique_name(self, check_csrf_token):
        """
        It should make sure the name stays unique when adding new cycles
        """
        from datetime import date
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams.studies import models, Session

        cycle = models.Cycle(name='week-1', title=u'Week 1', week=1)

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today(),
            cycles=[cycle])

        Session.add_all([study])
        Session.flush()

        with self.assertRaises(HTTPBadRequest) as cm:
            self.call_view(study['cycles'], testing.DummyRequest(
                json_body={
                    'name': 'week-1',
                    'title': 'Should fail',
                    'week': 2}))

        self.assertIn(
            'already exists',
            cm.exception.json['errors']['name'].lower())

    def test_edit_unique_name(self, check_csrf_token):
        """
        It should allow the cycle to be able to change its unique name
        """
        from datetime import date
        from pyramid import testing
        from occams.studies import models, Session

        self.config.add_route('cycle', '/{study}/{cycle}')

        cycle = models.Cycle(name='week-1', title=u'Week 1', week=1)

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today(),
            cycles=[cycle])

        Session.add_all([study])
        Session.flush()

        response = self.call_view(cycle, testing.DummyRequest(
            json_body={
                'name': 'somestudy',
                'title': cycle.title,
                'week': cycle.week}))

        self.assertIsNotNone(response)


@mock.patch('occams.studies.views.cycle.check_csrf_token')
class TestDeleteJson(IntegrationFixture):

    def call_view(self, context, request):
        from occams.studies.views.cycle import delete_json as view
        return view(context, request)

    def test_no_visit(self, check_csrf_token):
        """
        It should allow deleting of a cycle if it has no visits
        """

        from datetime import date
        from pyramid import testing
        from occams.studies import models, Session

        self.config.add_route('study', '/{study}')

        cycle = models.Cycle(name='week-1', title=u'Week 1', week=1)

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today(),
            cycles=[cycle])

        Session.add_all([study])
        Session.flush()

        self.call_view(cycle, testing.DummyRequest())
        self.assertEqual(0, study.cycles.count())

    def test_has_visits(self, check_csrf_token):
        """
        It should not allow deletion of a cycle if it has visit
        (unless administrator)
        """
        from datetime import date
        from pyramid import testing
        from pyramid.httpexceptions import HTTPForbidden
        from occams.studies import models, Session

        self.config.add_route('study', '/{study}')

        cycle = models.Cycle(name='week-1', title=u'Week 1', week=1)

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today(),
            cycles=[cycle])

        patient = models.Patient(
            site=models.Site(name='ucsd', title=u'UCSD'),
            pid=u'12345')

        enrollment = models.Enrollment(
            study=study,
            consent_date=date.today(),
            patient=patient)

        visit = models.Visit(
            patient=patient, visit_date=date.today(), cycles=[cycle])

        Session.add_all([study, enrollment, visit])
        Session.flush()

        # Should not be able to delete if not an admin
        self.config.testing_securitypolicy(permissive=False)
        with self.assertRaises(HTTPForbidden):
            self.call_view(cycle, testing.DummyRequest())

        self.config.testing_securitypolicy(permissive=True)
        self.call_view(cycle, testing.DummyRequest())
        self.assertEqual(0, study.cycles.count())
