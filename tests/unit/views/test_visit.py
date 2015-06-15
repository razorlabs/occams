import mock

from tests import IntegrationFixture


class TestCyclesJson(IntegrationFixture):

    def call_view(self, context, request):
        from occams_studies.views.visit import cycles_json as view
        return view(context, request)

    def test_by_query(self):
        """
        It should allow fetching via search terms (typical use)
        """
        from datetime import date
        from pyramid import testing
        from occams_studies import models, Session
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
        from occams_studies import models, Session
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
        from occams_studies.views.visit import validate_cycles as view
        return view(context, request)

    def test_call_success(self):
        """
        It should be able to validate cycles via GET (for AJAX request)
        """
        from datetime import date
        from pyramid import testing
        from occams_studies import models, Session
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
            params=MultiDict([
                ('cycles', ','.join(map(str, [cycle1.id, cycle2.id])))
            ])))

        self.assertTrue(response)

    def test_call_fail(self):
        """
        It should return an validation error string if the cycles are invalid
        """
        from pyramid import testing
        from webob.multidict import MultiDict
        from occams_studies import models, Session

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        Session.add_all([patient])
        Session.flush()

        response = self.call_view(patient['visits'], testing.DummyRequest(
            params=MultiDict([('cycles', '123')])))
        self.assertIn('not found', response.lower())


@mock.patch('occams_studies.views.visit.check_csrf_token')
class TestEditJson(IntegrationFixture):

    def call_view(self, context, request):
        from occams_studies.views.visit import edit_json as view
        return view(context, request)

    def test_valid_cycle(self, check_csrf_token):
        """
        It should only allow existing cycles
        """
        from datetime import date
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams_studies import models, Session

        self.config.add_route('studies.patient', '/{patient}')
        self.config.add_route('studies.visit', '/{patient}/{visit}')

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        Session.add_all([patient])
        Session.flush()

        with self.assertRaises(HTTPBadRequest) as cm:
            self.call_view(patient['visits'], testing.DummyRequest(
                json_body={
                    'cycles': ['123'],
                    'visit_date': str(date.today())}))

        self.assertIn(
            'not found', cm.exception.json['errors']['cycles-0'].lower())

    def test_unique_cycle(self, check_csrf_token):
        """
        It should not allow repeat cycles (unless it's interim)
        """
        from datetime import date, timedelta
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams_studies import models, Session

        self.config.add_route('studies.patient', '/{patient}')
        self.config.add_route('studies.visit', '/{patient}/{visit}')

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
                    'visit_date': str(date.today() + timedelta(days=1))}
                ))

        with self.assertRaises(HTTPBadRequest) as cm:
            make_request()

        self.assertIn(
            'already in use',
            cm.exception.json['errors']['cycles-0'].lower())

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
        from occams_studies import models, Session

        self.config.add_route('studies.patient', '/{patient}')
        self.config.add_route('studies.visit', '/{patient}/{visit}')

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
                'visit_date': str(date.today())}
            ))

        # New visits cannot share dates
        with self.assertRaises(HTTPBadRequest) as cm:
            self.call_view(patient['visits'], testing.DummyRequest(
                json_body={
                    'cycles': [cycle2.id],
                    'visit_date': str(date.today())}
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
        from occams_studies import models, Session

        self.config.add_route('studies.patient', '/{patient}')
        self.config.add_route('studies.visit', '/{patient}/{visit}')
        self.config.add_route('studies.visit_form', '/forms/{form}')

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
                'visit_date': str(date.today() + timedelta(days=1)),
                'include_forms': True}
            ))

        self.assertItemsEqual(
            ['form1'],
            [e['schema']['name'] for e in response['entities']])

        contexts = Session.query(models.Context).all()

        self.assertItemsEqual(
            ['patient', 'visit'],
            [c.external for c in contexts])

        visit = Session.query(models.Visit).get(response['id'])

        # Update to demonstrate forms can still be added on edit
        response = self.call_view(visit, testing.DummyRequest(
            json_body={
                'cycles': [cycle1.id, cycle2.id],
                'visit_date': str(date.today() + timedelta(days=1)),
                'include_forms': True}
            ))

        self.assertItemsEqual(
            ['form1', 'form2'],
            [e['schema']['name'] for e in response['entities']])

        contexts = Session.query(models.Context).all()

        self.assertItemsEqual(
            [(x, e['id'])
             for e in response['entities']
             for x in ('patient', 'visit')],
            [(c.external, c.entity_id) for c in contexts])

    def test_include_relative_form(self, check_csrf_token):
        """
        It should use the latest version of the form relative to the visit date
        """
        from datetime import date, timedelta
        from pyramid import testing
        from occams_studies import models, Session

        self.config.add_route('studies.patient', '/{patient}')
        self.config.add_route('studies.visit', '/{patient}/{visit}')
        self.config.add_route('studies.visit_form', '/forms/{form}')

        t0 = date.today()
        t1 = t0 + timedelta(days=1)
        t2 = t1 + timedelta(days=1)

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today())

        cycle1 = models.Cycle(name='week-1', title=u'', week=1)
        cycle1.schemata.update([
            models.Schema(name='form1', title=u'', publish_date=t0),
            models.Schema(name='form1', title=u'', publish_date=t2)])
        study.cycles.append(cycle1)

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        Session.add_all([patient, study])
        Session.flush()

        response = self.call_view(patient['visits'], testing.DummyRequest(
            json_body={
                'cycles': [cycle1.id],
                'visit_date': str(t1),
                'include_forms': True}
            ))

        self.assertEqual(1, len(response['entities']))
        self.assertEqual(
            str(t0), response['entities'][0]['schema']['publish_date'])

    def test_include_not_retracted_form(self, check_csrf_token):
        """
        It should not use retracted forms, even if there are the most recent
        """
        from datetime import date, timedelta
        from pyramid import testing
        from occams_studies import models, Session

        self.config.add_route('studies.patient', '/{patient}')
        self.config.add_route('studies.visit', '/{patient}/{visit}')
        self.config.add_route('studies.visit_form', '/forms/{form}')

        t0 = date.today()
        t1 = t0 + timedelta(days=1)
        t2 = t1 + timedelta(days=1)

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today())

        cycle1 = models.Cycle(name='week-1', title=u'', week=1)
        cycle1.schemata.update([
            models.Schema(name='form1', title=u'', publish_date=t0),
            models.Schema(name='form1', title=u'', publish_date=t2, retract_date=t2)])
        study.cycles.append(cycle1)

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        Session.add_all([patient, study])
        Session.flush()

        response = self.call_view(patient['visits'], testing.DummyRequest(
            json_body={
                'cycles': [cycle1.id],
                'visit_date': str(t2),
                'include_forms': True}
            ))

        self.assertEqual(1, len(response['entities']))
        self.assertEqual(
            str(t0), response['entities'][0]['schema']['publish_date'])

    def test_update_patient(self, check_csrf_token):
        """
        It should also mark the patient as modified
        """
        from datetime import date
        from pyramid import testing
        from occams_studies import models, Session

        self.config.add_route('studies.patient', '/{patient}')
        self.config.add_route('studies.visit', '/{patient}/{visit}')

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today())

        cycle1 = models.Cycle(study=study, name='week-1', title=u'', week=1)

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        Session.add_all([patient, study])
        Session.flush()

        old_modify_date = patient.modify_date

        self.call_view(patient['visits'], testing.DummyRequest(
            json_body={
                'cycles': [str(cycle1.id)],
                'visit_date': str(date.today())}))

        self.assertLess(old_modify_date, patient.modify_date)


@mock.patch('occams_studies.views.visit.check_csrf_token')
class TestDeleteJson(IntegrationFixture):

    def call_view(self, context, request):
        from occams_studies.views.visit import delete_json as view
        return view(context, request)

    def test_update_patient(self, check_csrf_token):
        """
        It should also mark the patient as modified
        """
        from datetime import date
        from pyramid import testing
        from occams_studies import models, Session

        self.config.add_route('studies.patient', '/{patient}')

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        visit = models.Visit(
            patient=patient,
            visit_date=date.today())

        Session.add_all([patient, visit])
        Session.flush()

        old_modify_date = patient.modify_date
        self.call_view(visit, testing.DummyRequest())
        self.assertLess(old_modify_date, patient.modify_date)

    def test_cascade_forms(self, check_csrf_token):
        """
        It should remove all visit-associated forms.
        """
        from datetime import date
        from pyramid import testing
        from occams_studies import models, Session

        self.config.add_route('studies.patient', '/{patient}')

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


@mock.patch('occams_studies.views.form.check_csrf_token')
class TestFormDeleteJson(IntegrationFixture):

    def call_view(self, context, request):
        from occams_studies.views.form import bulk_delete_json as view
        return view(context, request)

    def test_success(self, check_csrf_token):
        """
        It should allow removal of entities from a visit.
        """
        from datetime import date, timedelta
        from pyramid import testing
        from pyramid.httpexceptions import HTTPOk
        from occams_studies import models, Session

        cycle = models.Cycle(name='week-1', title=u'', week=1)

        schema = models.Schema(
            name=u'sample', title=u'', publish_date=date.today())

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today(),
            cycles=[cycle],
            schemata=set([schema]))

        site = models.Site(name=u'ucsd', title=u'UCSD')

        default_state = (
            Session.query(models.State)
            .filter_by(name=u'pending-entry')
            .one())

        t_a = date.today() + timedelta(days=5)
        patient_a = models.Patient(site=site, pid=u'12345')
        visit_a = models.Visit(
            patient=patient_a, cycles=[cycle], visit_date=t_a)
        entity_a_1 = models.Entity(
            schema=schema, collect_date=t_a, state=default_state)
        entity_a_2 = models.Entity(
            schema=schema, collect_date=t_a, state=default_state)
        entity_a_3 = models.Entity(
            schema=schema, collect_date=t_a, state=default_state)
        list(map(visit_a.entities.add, [entity_a_1, entity_a_2, entity_a_3]))

        Session.add_all([visit_a, study])
        Session.flush()

        response = self.call_view(visit_a['forms'], testing.DummyRequest(
            json_body={
                'forms': [entity_a_2.id, entity_a_3.id]
                }))

        # refresh the session so we can get a correct listing
        Session.expunge_all()
        visit_a = Session.query(models.Visit).get(visit_a.id)

        self.assertIsInstance(response, HTTPOk)
        self.assertItemsEqual(
            [e.id for e in [entity_a_1]],
            [e.id for e in visit_a.entities])
