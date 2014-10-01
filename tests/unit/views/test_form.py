import mock

from tests import IntegrationFixture


@mock.patch('occams.studies.views.form.check_csrf_token')
class TestAddJson(IntegrationFixture):

    def call_view(self, context, request):
        from occams.studies.views.form import add_json as view
        return view(context, request)

    def test_one(self, check_csrf_token):
        """
        It should allow adding a single form
        """
        from datetime import date, timedelta
        from pyramid import testing
        from pyramid.httpexceptions import HTTPOk
        from occams.studies import models, Session

        default_state = models.State(name='pending-entry', title=u'')

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

        t_a = date.today() + timedelta(days=5)
        patient_a = models.Patient(site=site, pid=u'12345')
        visit_a = models.Visit(
            patient=patient_a, cycles=[cycle], visit_date=t_a)

        Session.add_all([default_state, visit_a, study])
        Session.flush()

        response = self.call_view(visit_a['forms'], testing.DummyRequest(
            json_body={
                'schemata': [schema.id],
                }))

        # refresh the session so we can get a correct listing
        Session.expunge_all()
        visit_a = Session.query(models.Visit).get(visit_a.id)

        self.assertIsInstance(response, HTTPOk)
        self.assertEqual(1, len(visit_a.entities))

    def test_multiple(self, check_csrf_token):
        """
        It should allow adding multiple instances of the same form
        """
        from datetime import date, timedelta
        from pyramid import testing
        from pyramid.httpexceptions import HTTPOk
        from occams.studies import models, Session

        default_state = models.State(name='pending-entry', title=u'')

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

        t_a = date.today() + timedelta(days=5)
        patient_a = models.Patient(site=site, pid=u'12345')
        visit_a = models.Visit(
            patient=patient_a, cycles=[cycle], visit_date=t_a)

        Session.add_all([default_state, visit_a, study])
        Session.flush()

        response = self.call_view(visit_a['forms'], testing.DummyRequest(
            json_body={
                'schemata': [schema.id, schema.id],
                }))

        # refresh the session so we can get a correct listing
        Session.expunge_all()
        visit_a = Session.query(models.Visit).get(visit_a.id)

        self.assertIsInstance(response, HTTPOk)
        self.assertEqual(2, len(visit_a.entities))

    def test_not_in_study(self, check_csrf_token):
        """
        It should fail if the form is not part of the study
        """
        from datetime import date, timedelta
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams.studies import models, Session

        default_state = models.State(name='pending-entry', title=u'')

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
            cycles=[cycle])

        site = models.Site(name=u'ucsd', title=u'UCSD')

        t_a = date.today() + timedelta(days=5)
        patient_a = models.Patient(site=site, pid=u'12345')
        visit_a = models.Visit(
            patient=patient_a, cycles=[cycle], visit_date=t_a)

        Session.add_all([schema, default_state, visit_a, study])
        Session.flush()

        with self.assertRaises(HTTPBadRequest) as cm:
            self.call_view(visit_a['forms'], testing.DummyRequest(
                json_body={
                    'schemata': [schema.id],
                    }))

        self.assertIn(
            'is not part of the studies',
            cm.exception.json['errors']['schemata.0'])


@mock.patch('occams.studies.views.form.check_csrf_token')
class TestDeleteJson(IntegrationFixture):

    def call_view(self, context, request):
        from occams.studies.views.form import delete_json as view
        return view(context, request)

    def test_success(self, check_csrf_token):
        """
        It should allow moving entities to the resources from another visit
        """
        from datetime import date, timedelta
        from pyramid import testing
        from pyramid.httpexceptions import HTTPOk
        from occams.studies import models, Session

        default_state = models.State(name='pending-entry', title=u'')

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
