import mock

from tests import IntegrationFixture


class TestCyclesJson(IntegrationFixture):

    def call_view(self, context, request):
        from occams.studies.views.visit import cycles_json as view
        return view(context, request)

    def test_by_query(self):
        """
        It should allow fetching via search terms (typical use)
        """
        from datetime import date
        from pyramid import testing
        from occams.studies import models, Session
        from webob.multidict import MultiDict

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today())

        cycle1 = models.Cycle(name='week-1', title=u'Foo Week 1', week=1)
        cycle2 = models.Cycle(name='week-2', title=u'Bar Week 2', week=2)

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        study.cycles.append(cycle1)
        study.cycles.append(cycle2)

        Session.add_all([patient, study])
        Session.flush()

        response = self.call_view(patient['visits'], testing.DummyRequest(
            params=MultiDict([('q', u'foo')])))

        self.assertEqual(cycle1.id, response['cycles'][0]['id'])

    def test_by_ids(self):
        """
        It should allow search via direct ids (for pre-entered values)
        """
        from datetime import date
        from pyramid import testing
        from occams.studies import models, Session
        from webob.multidict import MultiDict

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today())

        cycle1 = models.Cycle(name='week-1', title=u'Foo Week 1', week=1)
        cycle2 = models.Cycle(name='week-2', title=u'Bar Week 2', week=2)

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        study.cycles.append(cycle1)
        study.cycles.append(cycle2)

        Session.add_all([patient, study])
        Session.flush()

        response = self.call_view(patient['visits'], testing.DummyRequest(
            params=MultiDict([('ids', cycle1.id)])))

        self.assertEqual(cycle1.id, response['cycles'][0]['id'])


class TestValidateCycles(IntegrationFixture):

    def call_view(self, context, request):
        from occams.studies.views.visit import validate_cycles as view
        return view(context, request)

    def test_call_success(self):
        """
        It should be able to validate cycles via GET (for AJAX request)
        """
        from datetime import date
        from pyramid import testing
        from occams.studies import models, Session
        from webob.multidict import MultiDict

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today())

        cycle1 = models.Cycle(name='week-1', title=u'Foo Week 1', week=1)
        cycle2 = models.Cycle(name='week-2', title=u'Bar Week 2', week=2)

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        study.cycles.append(cycle1)
        study.cycles.append(cycle2)

        Session.add_all([patient, study])
        Session.flush()

        response = self.call_view(patient['visits'], testing.DummyRequest(
            params=MultiDict([('cycles', cycle1.id), ('cycles', cycle2.id)])))

        self.assertTrue(response)

    def test_call_fail(self):
        """
        It should return an validation error string if the cycles are invalid
        """
        from pyramid import testing
        from webob.multidict import MultiDict
        from occams.studies import models, Session
        from occams.studies.validators import ERROR_NOT_FOUND

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        Session.add_all([patient])
        Session.flush()

        response = self.call_view(patient['visits'], testing.DummyRequest(
            params=MultiDict([('cycles', 123)])))

        self.assertEqual(ERROR_NOT_FOUND, response)


@mock.patch('occams.studies.views.visit.check_csrf_token')
class TestEditJson(IntegrationFixture):

    def call_view(self, context, request):
        from occams.studies.views.visit import edit_json as view
        return view(context, request)

    def test_valid_cycle(self, check_csrf_token):
        """
        It should only allow existing cycles
        """
        from datetime import date
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams.studies import models, Session
        from occams.studies.validators import ERROR_NOT_FOUND

        self.config.add_route('patient', '/{patient}')
        self.config.add_route('visit', '/{patient}/{visit}')

        Session.add(models.State(name='pending-entry', title=u''))

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        Session.add_all([patient])
        Session.flush()

        with self.assertRaises(HTTPBadRequest) as cm:
            self.call_view(patient['visits'], testing.DummyRequest(
                json_body={
                    'cycles': [123],
                    'visit_date': date.today()}))

        self.assertEqual(
            ERROR_NOT_FOUND, cm.exception.json['errors']['cycles.0'])

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

        self.assertIn(
            'is already used by visit',
            cm.exception.json['errors']['cycles.0'])

        # The exception is interims
        cycle.is_interim = True
        Session.flush()
        response = make_request()
        self.assertIsNotNone(response)

    def test_unique_visit_date(self, check_csrf_token):
        """
        It should not allow duplicate visit dates
        """
        from datetime import date
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

        cycle1 = models.Cycle(name='week-1', title=u'', week=1)
        cycle2 = models.Cycle(name='week-2', title=u'', week=2)

        study.cycles.append(cycle1)
        study.cycles.append(cycle2)

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        visit = models.Visit(
            patient=patient,
            cycles=[cycle1],
            visit_date=date.today())

        Session.add_all([patient, study, visit])
        Session.flush()

        # Update the visit, should allow to update the date
        self.call_view(visit, testing.DummyRequest(
            json_body={
                'cycles': [cycle2.id],
                'visit_date': date.today()}
            ))

        # New visits cannot share dates
        with self.assertRaises(HTTPBadRequest) as cm:
            self.call_view(patient['visits'], testing.DummyRequest(
                json_body={
                    'cycles': [cycle2.id],
                    'visit_date': date.today()}
                ))

        self.assertIn(
            'already exists',
            cm.exception.json['errors']['visit_date'])

    def test_include_forms(self, check_csrf_token):
        """
        It should allow the user to create cycle forms
        """
        from datetime import date, timedelta
        from pyramid import testing
        from occams.studies import models, Session

        self.config.add_route('patient', '/{patient}')
        self.config.add_route('visit', '/{patient}/{visit}')
        self.config.add_route('form', '/forms/{form}')

        Session.add(models.State(name='pending-entry', title=u''))

        form1 = models.Schema(
            name='form1', title=u'', publish_date=date.today())

        form2 = models.Schema(
            name='form2', title=u'', publish_date=date.today())

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today())

        cycle1 = models.Cycle(name='week-1', title=u'', week=1)
        cycle1.schemata.add(form1)

        cycle2 = models.Cycle(name='week-2', title=u'', week=2)
        cycle2.schemata.add(form2)

        study.cycles.append(cycle1)
        study.cycles.append(cycle2)

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        Session.add_all([patient, study])
        Session.flush()

        response = self.call_view(patient['visits'], testing.DummyRequest(
            json_body={
                'cycles': [cycle1.id],
                'visit_date': date.today() + timedelta(days=1),
                'include_forms': True}
            ))

        self.assertIn(
            'form1', [e['schema']['name'] for e in response['entities']])
        self.assertNotIn(
            'form2', [e['schema']['name'] for e in response['entities']])

        visit = Session.query(models.Visit).get(response['id'])

        # Update to demonstrate forms can still be added on edit
        response = self.call_view(visit, testing.DummyRequest(
            json_body={
                'cycles': [cycle1.id, cycle2.id],
                'visit_date': date.today() + timedelta(days=1),
                'include_forms': True}
            ))

        self.assertIn(
            'form1', [e['schema']['name'] for e in response['entities']])
        self.assertIn(
            'form2', [e['schema']['name'] for e in response['entities']])


@mock.patch('occams.studies.views.visit.check_csrf_token')
class TestDeleteJson(IntegrationFixture):

    def call_view(self, context, request):
        from occams.studies.views.visit import delete_json as view
        return view(context, request)

    def test_cascade_forms(self, check_csrf_token):
        """
        It should remove all visit-associated forms.
        """
        from datetime import date
        from pyramid import testing
        from occams.studies import models, Session

        self.config.add_route('patient', '/{patient}')

        schema = models.Schema(
            name=u'sample',
            title=u'Some Sample',
            publish_date=date.today())

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today())

        cycle = models.Cycle(
            name=u'week-10',
            title=u'Week 10',
            week=10)

        study.cycles.append(cycle)

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        enrollment = models.Enrollment(
            study=study,
            patient=patient,
            consent_date=date.today())

        visit = models.Visit(
            patient=patient,
            cycles=[cycle],
            visit_date=date.today())

        visit.entities.add(models.Entity(
            schema=schema,
            collect_date=date.today()))

        Session.add_all([patient, enrollment, study, visit])
        Session.flush()

        visit_id = visit.id

        self.call_view(visit, testing.DummyRequest())

        self.assertIsNone(Session.query(models.Visit).get(visit_id))
        self.assertEquals(0, Session.query(models.Entity).count())
