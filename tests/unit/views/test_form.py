import mock

from tests import IntegrationFixture


class TestViewJSON(IntegrationFixture):

    def call_view(self, context, request):
        from occams_studies.views.form import view_json as view
        return view(context, request)

    def test_with_state(self):
        """
        It should generate state data is available
        """
        from pyramid import testing
        from occams_studies import models, Session
        from datetime import date

        myfirst = models.Schema(
            name=u'myfirst',
            title=u'My First Schema',
            publish_date=date.today()
        )
        mydata = models.Entity(
            schema=myfirst,
            state=(
                Session.query(models.State)
                .filter_by(name=u'pending-entry')
                .one()))
        Session.add(mydata)
        Session.flush()
        mydata.__parent__ = mock.MagicMock()
        mydata.__parent__.__parent__ = mock.MagicMock()

        request = testing.DummyRequest()
        request.session.changed = mock.Mock()
        response = self.call_view(mydata, request)

        self.assertIsNotNone(response['state'])

    def test_without_state(self):
        """
        It should generate none if no state data is available
        """
        from pyramid import testing
        from occams_studies import models, Session
        from datetime import date

        myfirst = models.Schema(
            name=u'myfirst',
            title=u'My First Schema',
            publish_date=date.today()
        )
        mydata = models.Entity(schema=myfirst)
        Session.add(mydata)
        Session.flush()
        mydata.__parent__ = mock.MagicMock()
        mydata.__parent__.__parent__ = mock.MagicMock()

        request = testing.DummyRequest()
        request.session.changed = mock.Mock()
        response = self.call_view(mydata, request)

        self.assertIsNone(response['state'])


@mock.patch('occams_studies.views.form.check_csrf_token')
class TestAddJSON(IntegrationFixture):

    def call_view(self, context, request):
        from occams_studies.views.form import add_json as view
        return view(context, request)

    def test_add_to_patient(self, check_csrf_token):
        from datetime import date
        from pyramid import testing
        from occams_studies import models, Session

        self.config.add_route('studies.patient_form', '/p/f/{form}')

        schema = models.Schema(
            name=u'schema',
            title=u'Schema',
            publish_date=date.today())

        study = models.Study(
            name='some-study',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today(),
            schemata=set([schema]))

        site = models.Site(name=u'somewhere', title=u'Somewhere')
        patient = models.Patient(pid=u'12345', site=site)

        Session.add_all([study, patient])
        Session.flush()

        request = testing.DummyRequest(json_body={
            'schema': schema.id,
            'collect_date': str(date.today()),
        })
        factory = models.FormFactory(request)
        factory.__parent__ = patient
        self.call_view(factory, request)

        contexts = Session.query(models.Context).all()

        self.assertEquals(1, len(contexts))
        self.assertEquals(schema, contexts[0].entity.schema)

    def test_add_to_visit(self, check_csrf_token):
        from datetime import date
        from pyramid import testing
        from occams_studies import models, Session

        self.config.add_route('studies.visit_form', '/v/f/{form}')

        schema = models.Schema(
            name=u'schema',
            title=u'Schema',
            publish_date=date.today())

        study = models.Study(
            name='some-study',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today(),
            schemata=set([schema]))

        cycle = models.Cycle(
            study=study,
            name=u'cycle-1',
            title=u'Cycle')

        site = models.Site(name=u'somewhere', title=u'Somewhere')
        patient = models.Patient(pid=u'12345', site=site)

        visit = models.Visit(
            patient=patient, visit_date=date.today(), cycles=[cycle])

        Session.add_all([study, patient, visit])
        Session.flush()

        request = testing.DummyRequest(json_body={
            'schema': schema.id,
            'collect_date': str(date.today()),
        })
        factory = models.FormFactory(request)
        factory.__parent__ = visit
        self.call_view(factory, request)

        contexts = Session.query(models.Context).all()

        self.assertEquals(2, len(contexts))
        self.assertItemsEqual(
            ['patient', 'visit'],
            [c.external for c in contexts])

    def test_multiple(self, check_csrf_token):
        """
        It should allow adding multiple instances of the same form
        TODO: cant do multiple, no time
        """

    def test_not_in_study(self, check_csrf_token):
        """
        It should fail if the form is not part of the study
        """
        from datetime import date, timedelta
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
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
            cycles=[cycle])

        site = models.Site(name=u'ucsd', title=u'UCSD')

        t_a = date.today() + timedelta(days=5)
        patient_a = models.Patient(site=site, pid=u'12345')
        visit_a = models.Visit(
            patient=patient_a, cycles=[cycle], visit_date=t_a)

        Session.add_all([schema, visit_a, study])
        Session.flush()

        with self.assertRaises(HTTPBadRequest) as cm:
            self.call_view(visit_a['forms'], testing.DummyRequest(
                json_body={
                    'schema': schema.id,
                    }))

        self.assertIn(
            'is not part of the studies',
            cm.exception.json['errors']['schema'])
