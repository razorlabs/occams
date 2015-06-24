import mock

from tests import IntegrationFixture


def _register_routes(config):
    config.add_route('studies.main', '/')
    config.add_route('studies.patient', '/p/{patient}')
    config.add_route('studies.site',    '/s/{site}')
    config.add_route('studies.reference_type',    '/r/{reference_type}')
    config.add_route('studies.enrollment', '/e/{enrollment}')
    config.add_route('studies.enrollment_randomization', '/e/{enrollment}/r')
    config.add_route('studies.enrollment_termination', '/e/{enrollment}/t')


class TestView(IntegrationFixture):

    def call_view(self, context, request):
        from occams_studies.views.patient import view
        return view(context, request)

    def test_track_recently_viewed(self):
        """
        It should track recently viewed patients
        """
        from pyramid import testing
        from occams_studies import models, Session

        _register_routes(self.config)

        site_la = models.Site(name=u'la', title=u'LA')
        patient = models.Patient(site=site_la, pid=u'12345')
        Session.add(patient)
        Session.flush()

        request = testing.DummyRequest()
        request.session.changed = mock.Mock()
        self.call_view(patient, request)

        self.assertIn('12345', request.session['viewed'])
        self.assertEquals(1, len(request.session['viewed']))
        self.assertTrue(request.session.changed.called)

    def test_track_limit(self):
        """
        It should only keep track of the last 10 recently viewed patients
        """
        from collections import OrderedDict
        from datetime import datetime
        from pyramid import testing
        from occams_studies import models, Session

        _register_routes(self.config)

        site_la = models.Site(name=u'la', title=u'LA')
        patient = models.Patient(site=site_la, pid=u'12345')
        Session.add(patient)
        Session.flush()

        request = testing.DummyRequest()
        request.session['viewed'] = OrderedDict()
        request.session.changed = mock.Mock()

        previous = [str(i) for i in range(10)]

        for pid in previous:
            request.session['viewed'][pid] = \
                {'pid': pid, 'view_date': datetime.now()}

        self.call_view(patient, request)

        self.assertIn('12345', request.session['viewed'])
        self.assertNotIn(previous[0], request.session['viewed'])
        self.assertEquals(10, len(request.session['viewed']))


class TestSearchJson(IntegrationFixture):

    def call_view(self, context, request):
        from occams_studies.views.patient import search_json as view
        return view(context, request)

    def test_by_pid(self):
        """
        It should search by PID
        """
        from pyramid import testing
        from occams_studies import models, Session
        from webob.multidict import MultiDict

        _register_routes(self.config)

        site_la = models.Site(name=u'la', title=u'LA')
        patient = models.Patient(site=site_la, pid=u'12345')
        Session.add_all([site_la, patient])
        Session.flush()

        request = testing.DummyRequest(
            params=MultiDict([
                ('query', u'12345')
            ]))
        response = self.call_view(models.PatientFactory(request), request)
        self.assertEquals(patient.pid, response['patients'][0]['pid'])

    def test_by_enrollment_number(self):
        """
        It should be able to search by Enrollment Number
        """
        from datetime import date
        from pyramid import testing
        from occams_studies import models, Session
        from webob.multidict import MultiDict

        _register_routes(self.config)

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today())
        site_la = models.Site(name=u'la', title=u'LA')
        patient = models.Patient(
            site=site_la, pid=u'12345',
            enrollments=[
                models.Enrollment(
                    study=study,
                    reference_number=u'xyz',
                    consent_date=date.today())
                ])
        Session.add_all([site_la, patient])
        Session.flush()

        request = testing.DummyRequest(
            params=MultiDict([
                ('query', u'xyz')
                ]))
        response = self.call_view(models.PatientFactory(request), request)
        self.assertEquals(patient.pid, response['patients'][0]['pid'])

    def test_by_reference_number(self):
        """
        It should be able to search by external ID
        """
        from pyramid import testing
        from occams_studies import models, Session
        from webob.multidict import MultiDict

        _register_routes(self.config)

        site_la = models.Site(name=u'la', title=u'LA')
        patient = models.Patient(
            site=site_la, pid=u'12345',
            references=[
                models.PatientReference(
                    reference_type=models.ReferenceType(
                        name=u'ext',
                        title=u'External ID'),
                    reference_number=u'05-01-0000-5')
                ])
        Session.add_all([site_la, patient])
        Session.flush()

        request = testing.DummyRequest(
            params=MultiDict([
                ('query', u'05-01')
                ]))
        response = self.call_view(models.PatientFactory(request), request)
        self.assertEquals(patient.pid, response['patients'][0]['pid'])


@mock.patch('occams_studies.views.patient.check_csrf_token')
class TestEditJson(IntegrationFixture):

    def call_view(self, context, request):
        from occams_studies.views.patient import edit_json as view
        return view(context, request)

    def test_site(self, check_csrf_token):
        """
        It should update sites
        """
        from pyramid import testing
        from occams_studies import models, Session

        _register_routes(self.config)

        site_la = models.Site(name=u'la', title=u'LA')
        site_sd = models.Site(name=u'sd', title=u'SD')
        patient = models.Patient(site=site_la, pid=u'12345')
        Session.add_all([site_la, site_sd, patient])
        Session.flush()

        request = testing.DummyRequest(
            json_body={'site': site_sd.id})

        self.call_view(patient, request)
        self.assertTrue(check_csrf_token.called)
        self.assertEquals(patient.site.id, site_sd.id)

    def test_site_invalid(self, check_csrf_token):
        """
        It should enforce valid sites
        """
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams_studies import models, Session

        _register_routes(self.config)

        site_la = models.Site(name=u'la', title=u'LA')
        patient = models.Patient(site=site_la, pid=u'12345')
        Session.add_all([site_la, patient])
        Session.flush()

        request = testing.DummyRequest(
            json_body={'site': site_la.id + 100})

        with self.assertRaises(HTTPBadRequest) as cm:
            self.call_view(patient, request)
        self.assertTrue(check_csrf_token.called)
        self.assertIn(
            'not found', cm.exception.json['errors']['site'].lower())

    def test_reference_type_invalid(self, check_csrf_token):
        """
        It should enforce valid reference_types
        """
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams_studies import models, Session

        _register_routes(self.config)

        site_la = models.Site(name=u'la', title=u'LA')
        patient = models.Patient(site=site_la, pid=u'12345')
        Session.add(patient)
        Session.flush()

        request = testing.DummyRequest(
            json_body={
                'site': patient.site.id,
                'references': [
                    {'reference_type': 123,
                     'reference_number': u'ABC'}]})
        with self.assertRaises(HTTPBadRequest) as cm:
            self.call_view(patient, request)
        self.assertTrue(check_csrf_token.called)
        self.assertIn(
            'not found',
            cm.exception.json['errors']['references-0-reference_type'].lower())

    def test_reference_valid_number(self, check_csrf_token):
        """
        It should check reference patterns if they are supported by the type
        """
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams_studies import models, Session

        _register_routes(self.config)

        site_la = models.Site(name=u'la', title=u'LA')
        reftype = models.ReferenceType(
            name=u'foo', title=u'Foo',
            reference_pattern=u'^[0-9]+$')
        patient = models.Patient(site=site_la, pid=u'12345')
        Session.add_all([patient, reftype])
        Session.flush()

        request = testing.DummyRequest(
            json_body={
                'site': site_la.id,
                'references': [
                    {'reference_type': reftype.id,
                     'reference_number': u'XYZ'}]})
        with self.assertRaises(HTTPBadRequest) as cm:
            self.call_view(patient, request)
        self.assertTrue(check_csrf_token.called)
        self.assertIn(
            'Invalid format',
            cm.exception.json['errors']['references-0-reference_number'])

    def test_reference_unique(self, check_csrf_token):
        """
        It should enforce unique reference_types
        """
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams_studies import models, Session

        _register_routes(self.config)

        site_la = models.Site(name=u'la', title=u'LA')
        reftype = models.ReferenceType(name=u'foo', title=u'Foo')
        other = models.Patient(site=site_la, pid=u'ABCDE', references=[
            models.PatientReference(
                reference_type=reftype,
                reference_number=u'XYZ')])
        patient = models.Patient(site=site_la, pid=u'12345')
        Session.add_all([patient, other])
        Session.flush()

        request = testing.DummyRequest(
            json_body={
                'site': site_la.id,
                'references': [
                    {'reference_type': reftype.id,
                     'reference_number': u'XYZ'}]})
        with self.assertRaises(HTTPBadRequest) as cm:
            self.call_view(patient, request)
        self.assertTrue(check_csrf_token.called)
        self.assertIn(
            'Already assigned',
            cm.exception.json['errors']['references-0-reference_number'])

    def test_references(self, check_csrf_token):
        """
        It should update references
        """
        from pyramid import testing
        from occams_studies import models, Session

        _register_routes(self.config)

        reftype1 = models.ReferenceType(name=u'foo', title=u'Foo')
        reftype2 = models.ReferenceType(name=u'bar', title=u'Bar')
        site_la = models.Site(name=u'la', title=u'LA')
        patient = models.Patient(site=site_la, pid=u'12345')
        patient.references = [
            models.PatientReference(
                reference_type=reftype1,
                reference_number=u'XYZ'),
            models.PatientReference(
                reference_type=reftype2,
                reference_number=u'ABC')
            ]
        Session.add_all([site_la,  patient])
        Session.flush()

        request = testing.DummyRequest(
            json_body={
                'site': patient.site.id,
                'references': [
                    {'reference_type': reftype1.id,
                     'reference_number': u'XYZ'},
                    {'reference_type': reftype1.id,
                     'reference_number': u'RST'}]})
        self.call_view(patient, request)
        self.assertTrue(check_csrf_token.called)
        self.assertItemsEqual(
            [(reftype1.id, u'XYZ'), (reftype1.id, u'RST')],
            [(r.reference_type.id, r.reference_number)
             for r in patient.references])

    @mock.patch('occams_studies.views.patient.generate')
    def test_generate_pid(self, generate, check_csrf_token):
        """
        It should generate a PID for new patients
        """
        from pyramid import testing
        from occams_studies import models, Session

        _register_routes(self.config)

        site_la = models.Site(name=u'la', title=u'LA')
        reftype = models.ReferenceType(name=u'foo', title=u'FOO')
        Session.add_all([site_la, reftype])
        Session.flush()

        request = testing.DummyRequest(
            json_body={
                'site': site_la.id,
                'references': [
                    {'reference_type': reftype.id,
                     'reference_number': u'ABC'}
                ]})

        # Fake generate a PID, the roster should unit test this
        generate.return_value = u'12345'

        response = self.call_view(models.PatientFactory(request), request)

        generate.assert_called_with(site_la.name)
        self.assertTrue(check_csrf_token.called)
        self.assertEqual(u'12345', response['pid'])
        self.assertEqual(site_la.id, response['site']['id'])
        self.assertItemsEqual(
            [(reftype.id, u'ABC')],
            [(r['reference_type']['id'], r['reference_number'])
             for r in response['references']])


@mock.patch('occams_studies.views.patient.check_csrf_token')
class TestDeleteJson(IntegrationFixture):

    def call_view(self, context, request):
        from occams_studies.views.patient import delete_json as view
        return view(context, request)

    def test_delete(self, check_csrf_token):
        """
        It should allow a valid principal to delete a patient
        """
        from collections import OrderedDict
        from pyramid import testing
        from occams_studies import models, Session

        _register_routes(self.config)

        site_la = models.Site(name=u'la', title=u'LA')
        patient = models.Patient(site=site_la, pid=u'12345')
        Session.add(patient)
        Session.flush()
        patient_id = patient.id

        request = testing.DummyRequest()
        request.session['viewed'] = OrderedDict([('12345', {})])
        request.session.changed = mock.Mock()
        self.call_view(patient, request)

        self.assertIsNone(Session.query(models.Patient).get(patient_id))
        self.assertNotIn(u'12345', request.session['viewed'])

    def test_cascade_entities(self, check_csrf_token):
        """
        It should delete associated entities
        """

        from datetime import date
        from pyramid import testing
        from occams_studies import models, Session

        _register_routes(self.config)

        schema = models.Schema(
            name=u'somepatientform',
            title=u'Some Patient Form',
            publish_date=date.today())
        entity = models.Entity(
            collect_date=date.today(),
            schema=schema)
        patient = models.Patient(
            site=models.Site(name=u'la', title=u'LA'),
            pid=u'12345')
        patient.entities.add(entity)
        Session.add_all([patient, entity, schema])
        Session.flush()

        patient = Session.query(models.Patient).one()

        self.call_view(patient, testing.DummyRequest())

        self.assertEquals(0, Session.query(models.Entity).count())
