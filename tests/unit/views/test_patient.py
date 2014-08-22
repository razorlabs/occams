import mock

from tests import IntegrationFixture


class TestGetPatient(IntegrationFixture):

    def test_found(self):
        """
        It should be able to find the patient form the URL matchdict
        """
        from pyramid import testing
        from occams.studies import models, Session
        from occams.studies.views.patient import get_patient

        patient = models.Patient(
            site=models.Site(name=u'la', title=u'LA'),
            pid=u'12345')
        Session.add(patient)
        Session.flush()

        found = get_patient(testing.DummyRequest(
            matchdict={'patient': patient.pid}))

        self.assertEqual(patient.id, found.id)

    def test_not_found(self):
        """
        It should raise 404 if the patient is not found in the system
        """
        from pyramid import testing
        from pyramid.httpexceptions import HTTPNotFound
        from occams.studies.views.patient import get_patient

        with self.assertRaises(HTTPNotFound):
            get_patient(testing.DummyRequest(
                matchdict={'patient': u'1D0NT3X1ST'}))


class TestSearch(IntegrationFixture):

    def call_view(self, request):
        from occams.studies.views.patient import search
        return search(request)

    def test_simple(self):
        assert False, "not implemented"


@mock.patch('occams.studies.views.patient.check_csrf_token')
def TestAddJson(IntegrationFixture):

    def call_view(self, request):
        from occams.studies.views.patient import add_json as view
        return view(request)

    @mock.path('occams.studies.views.patient.generate')
    def test_generate_pid(self, generate, check_csrf_token):
        """
        It should generate a PID for new patients
        """
        from pyramid import testing
        from occams.studies import models, Session

        self.config.add_route('patient', '/patients/{patient}')

        site_la = models.Site(name=u'la', title=u'LA')
        reftype = models.ReferenceType(name=u'foo', title=u'FOO')
        Session.add(site_la)
        Session.flush()

        request = testing.DummyRequest(
            json_body={
                'site_id': site_la.id,
                'references': [
                    {'reference_type_id': reftype.id,
                     'referecence_number': u'ABC'}
                ]})

        # Fake generate a PID, the roster should unit test this
        generate.ret_val = u'12345'

        response = self.call_view(request)

        generate.assert_called_with(site_la.name)
        self.assertTrue(check_csrf_token.called)
        self.assertEqual(u'12345', response['pid'])
        self.assertEqual(site_la.id, response['site_id'])
        self.assertItemsEqual(
            [(reftype.id, u'ABC')],
            [(r['reference_type_id'], r['reference_numner'])
             for r in response['references']])


@mock.patch('occams.studies.views.patient.check_csrf_token')
class TestEditJson(IntegrationFixture):

    def call_view(self, request):
        from occams.studies.views.patient import edit_json as view
        return view(request)

    def test_site(self, check_csrf_token):
        """
        It should update sites
        """
        from pyramid import testing
        from occams.studies import models, Session

        self.config.add_route('patient', '/patients/{patient}')

        site_la = models.Site(name=u'la', title=u'LA')
        site_sd = models.Site(name=u'sd', title=u'SD')
        patient = models.Patient(site=site_la, pid=u'12345')
        Session.add_all([site_la, site_sd, patient])
        Session.flush()

        request = testing.DummyRequest(
            matchdict={'patient': patient.pid},
            json_body={'site_id': site_sd.id})

        self.call_view(request)
        self.assertTrue(check_csrf_token.called)
        self.assertEquals(patient.site.id, site_sd.id)

    def test_site_invalid(self, check_csrf_token):
        """
        It should enforce valid sites
        """
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams.studies import models, Session

        self.config.add_route('patient', '/patients/{patient}')

        site_la = models.Site(name=u'la', title=u'LA')
        patient = models.Patient(site=site_la, pid=u'12345')
        Session.add_all([site_la, patient])
        Session.flush()

        request = testing.DummyRequest(
            matchdict={'patient': patient.pid},
            # Use an id other than the one in the database
            json_body={'site_id': site_la.id + 100})

        with self.assertRaises(HTTPBadRequest) as cm:
            self.call_view(request)
        self.assertTrue(check_csrf_token.called)
        self.assertIn('site', cm.exception.json['validation_errors'][0])

    def test_reference_type_invalid(self, check_csrf_token):
        """
        It should enforce valid reference_types
        """
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams.studies import models, Session

        self.config.add_route('patient', '/patients/{patient}')

        site_la = models.Site(name=u'la', title=u'LA')
        patient = models.Patient(site=site_la, pid=u'12345')
        Session.add(patient)
        Session.flush()

        request = testing.DummyRequest(
            matchdict={'patient': patient.pid},
            json_body={'references': [
                {'reference_type_id': 123,
                 'reference_number': u'ABC'}]})
        with self.assertRaises(HTTPBadRequest) as cm:
            self.call_view(request)
        self.assertTrue(check_csrf_token.called)
        self.assertIn('type', cm.exception.json['validation_errors'][0])

    def test_reference_valid_number(self, check_csrf_token):
        """
        It should check reference patterns if they are supported by the type
        """
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams.studies import models, Session

        self.config.add_route('patient', '/patients/{patient}')

        site_la = models.Site(name=u'la', title=u'LA')
        reftype = models.ReferenceType(
            name=u'foo', title=u'Foo',
            reference_pattern=u'^[0-9]$')
        patient = models.Patient(site=site_la, pid=u'12345')
        Session.add_all([patient, reftype])
        Session.flush()

        request = testing.DummyRequest(
            matchdict={'patient': patient.pid},
            json_body={'references': [
                {'reference_type_id': reftype.id,
                 'reference_number': u'XYZ'}]})
        with self.assertRaises(HTTPBadRequest) as cm:
            self.call_view(request)
        self.assertTrue(check_csrf_token.called)
        self.assertIn('not a valid format',
                      cm.exception.json['validation_errors'][0])

    def test_reference_unique(self, check_csrf_token):
        """
        It should enforce unique reference_types
        """
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams.studies import models, Session

        self.config.add_route('patient', '/patients/{patient}')

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
            matchdict={'patient': patient.pid},
            json_body={'references': [
                {'reference_type_id': reftype.id,
                 'reference_number': u'XYZ'}]})
        with self.assertRaises(HTTPBadRequest) as cm:
            self.call_view(request)
        self.assertTrue(check_csrf_token.called)
        self.assertIn('already assigned',
                      cm.exception.json['validation_errors'][0])

    def test_references(self, check_csrf_token):
        """
        It should update references
        """
        from pyramid import testing
        from occams.studies import models, Session

        self.config.add_route('patient', '/patients/{patient}')

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
            matchdict={'patient': patient.pid},
            json_body={'references': [
                {'reference_type_id': reftype1.id,
                 'reference_number': u'XYZ'},
                {'reference_type_id': reftype1.id,
                 'reference_number': u'RST'}]})
        self.call_view(request)
        self.assertTrue(check_csrf_token.called)
        self.assertItemsEqual(
            [(reftype1.id, u'XYZ'), (reftype1.id, u'RST')],
            [(r.reference_type.id, r.reference_number)
             for r in patient.references])


@mock.patch('occams.studies.views.patient.check_csrf_token')
class TestDeleteJSON(IntegrationFixture):

    def call_view(self, request):
        from occams.studies.views.patient import delete_json as view
        return view(request)

    def test_delete(self, check_csrf_token):
        """
        It should allow a valid principal to delete a patient
        """
        from pyramid import testing
        from occams.studies import models, Session

        self.config.add_route('home', '/home')

        site_la = models.Site(name=u'la', title=u'LA')
        patient = models.Patient(site=site_la, pid=u'12345')
        Session.add(patient)
        Session.flush()
        patient_id = patient.id

        self.call_view(testing.DummyRequest(
            matchdict={'patient': patient.pid}))

        self.assertIsNone(Session.query(models.Patient).get(patient_id))
