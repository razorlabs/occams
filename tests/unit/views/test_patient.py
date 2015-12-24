import pytest


@pytest.yield_fixture
def check_csrf_token(config):
    import mock
    name = 'occams_studies.views.patient.check_csrf_token'
    with mock.patch(name) as patch:
        yield patch


class TestView:

    def _call_fut(self, *args, **kw):
        from occams_studies.views.patient import view
        return view(*args, **kw)

    def test_track_recently_viewed(self, req, db_session):
        """
        It should track recently viewed patients
        """
        import mock
        from occams_studies import models

        site_la = models.Site(name=u'la', title=u'LA')
        patient = models.Patient(site=site_la, pid=u'12345')
        db_session.add(patient)
        db_session.flush()

        req.session.changed = mock.Mock()
        self._call_fut(patient, req)

        assert '12345' in req.session['viewed']
        assert 1 == len(req.session['viewed'])
        assert req.session.changed.called

    def test_track_limit(self, req, db_session):
        """
        It should only keep track of the last 10 recently viewed patients
        """
        from collections import OrderedDict
        from datetime import datetime
        import mock
        from occams_studies import models

        site_la = models.Site(name=u'la', title=u'LA')
        patient = models.Patient(site=site_la, pid=u'12345')
        db_session.add(patient)
        db_session.flush()

        req.session['viewed'] = OrderedDict()
        req.session.changed = mock.Mock()

        previous = [str(i) for i in range(10)]

        for pid in previous:
            req.session['viewed'][pid] = \
                {'pid': pid, 'view_date': datetime.now()}

        self._call_fut(patient, req)

        assert '12345' in req.session['viewed']
        assert previous[0] not in req.session['viewed']
        assert 10 == len(req.session['viewed'])


class TestSearchJson:

    def _call_fut(self, *args, **kw):
        from occams_studies.views.patient import search_json as view
        return view(*args, **kw)

    def test_by_pid(self, req, db_session):
        """
        It should search by PID
        """
        from occams_studies import models
        from webob.multidict import MultiDict

        site_la = models.Site(name=u'la', title=u'LA')
        patient = models.Patient(site=site_la, pid=u'12345')
        db_session.add_all([site_la, patient])
        db_session.flush()

        req.GET = MultiDict([('query', u'12345')])
        res = self._call_fut(models.PatientFactory(req), req)
        assert patient.pid == res['patients'][0]['pid']

    def test_by_enrollment_number(self, req, db_session):
        """
        It should be able to search by Enrollment Number
        """
        from datetime import date
        from occams_studies import models
        from webob.multidict import MultiDict

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
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
        db_session.add_all([site_la, patient])
        db_session.flush()

        req.GET = MultiDict([('query', u'xyz')])
        res = self._call_fut(models.PatientFactory(req), req)
        assert patient.pid == res['patients'][0]['pid']

    def test_by_reference_number(self, req, db_session):
        """
        It should be able to search by external ID
        """
        from occams_studies import models
        from webob.multidict import MultiDict

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
        db_session.add_all([site_la, patient])
        db_session.flush()

        req.GET = MultiDict([('query', u'05-01')])
        res = self._call_fut(models.PatientFactory(req), req)
        assert patient.pid == res['patients'][0]['pid']


class TestEditJson:

    def _call_fut(self, *args, **kw):
        from occams_studies.views.patient import edit_json as view
        return view(*args, **kw)

    def test_site(self, req, db_session, check_csrf_token):
        """
        It should update sites
        """
        from occams_studies import models

        site_la = models.Site(name=u'la', title=u'LA')
        site_sd = models.Site(name=u'sd', title=u'SD')
        patient = models.Patient(site=site_la, pid=u'12345')
        db_session.add_all([site_la, site_sd, patient])
        db_session.flush()

        req.json_body = {'site': site_sd.id}

        self._call_fut(patient, req)
        assert check_csrf_token.called
        assert patient.site.id == site_sd.id

    def test_site_invalid(self, req, db_session, check_csrf_token):
        """
        It should enforce valid sites
        """
        from pyramid.httpexceptions import HTTPBadRequest
        from occams_studies import models

        site_la = models.Site(name=u'la', title=u'LA')
        patient = models.Patient(site=site_la, pid=u'12345')
        db_session.add_all([site_la, patient])
        db_session.flush()

        req.json_body = {'site': site_la.id + 100}

        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(patient, req)
        assert check_csrf_token.called
        assert 'not found' in excinfo.value.json['errors']['site'].lower()

    def test_reference_type_invalid(self, req, db_session, check_csrf_token):
        """
        It should enforce valid reference_types
        """
        from pyramid.httpexceptions import HTTPBadRequest
        from occams_studies import models

        site_la = models.Site(name=u'la', title=u'LA')
        patient = models.Patient(site=site_la, pid=u'12345')
        db_session.add(patient)
        db_session.flush()

        req.json_body = {
            'site': patient.site.id,
            'references': [
                {'reference_type': 123,
                 'reference_number': u'ABC'}]
        }

        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(patient, req)

        assert check_csrf_token.called
        assert 'not found' in \
            excinfo.value.json['errors']['references-0-reference_type'].lower()

    def test_reference_valid_number(self, req, db_session, check_csrf_token):
        """
        It should check reference patterns if they are supported by the type
        """
        from pyramid.httpexceptions import HTTPBadRequest
        from occams_studies import models

        site_la = models.Site(name=u'la', title=u'LA')
        reftype = models.ReferenceType(
            name=u'foo', title=u'Foo',
            reference_pattern=u'^[0-9]+$')
        patient = models.Patient(site=site_la, pid=u'12345')
        db_session.add_all([patient, reftype])
        db_session.flush()

        req.json_body = {
            'site': site_la.id,
            'references': [
                {'reference_type': reftype.id,
                 'reference_number': u'XYZ'}]
        }
        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(patient, req)
        assert check_csrf_token.called
        assert 'Invalid format' in \
            excinfo.value.json['errors']['references-0-reference_number']

    def test_reference_unique(self, req, db_session, check_csrf_token):
        """
        It should enforce unique reference_types
        """
        from pyramid.httpexceptions import HTTPBadRequest
        from occams_studies import models

        site_la = models.Site(name=u'la', title=u'LA')
        reftype = models.ReferenceType(name=u'foo', title=u'Foo')
        other = models.Patient(site=site_la, pid=u'ABCDE', references=[
            models.PatientReference(
                reference_type=reftype,
                reference_number=u'XYZ')])
        patient = models.Patient(site=site_la, pid=u'12345')
        db_session.add_all([patient, other])
        db_session.flush()

        req.json_body = {
            'site': site_la.id,
            'references': [
                {'reference_type': reftype.id,
                 'reference_number': u'XYZ'}]
        }

        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(patient, req)

        assert check_csrf_token.called
        assert 'Already assigned' in \
            excinfo.value.json['errors']['references-0-reference_number']

    def test_references(self, req, db_session, check_csrf_token):
        """
        It should update references
        """
        from occams_studies import models

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
        db_session.add_all([site_la,  patient])
        db_session.flush()

        req.json_body = {
            'site': patient.site.id,
            'references': [
                {'reference_type': reftype1.id,
                 'reference_number': u'XYZ'},
                {'reference_type': reftype1.id,
                 'reference_number': u'RST'}]
        }

        self._call_fut(patient, req)

        assert check_csrf_token.called
        assert sorted([(reftype1.id, u'XYZ'), (reftype1.id, u'RST')]) == \
            sorted([(r.reference_type.id, r.reference_number)
                    for r in patient.references])

    def test_generate_pid(self, req, db_session, check_csrf_token):
        """
        It should generate a PID for new patients
        """
        import mock
        from occams_studies import models

        site_la = models.Site(name=u'la', title=u'LA')
        reftype = models.ReferenceType(name=u'foo', title=u'FOO')
        db_session.add_all([site_la, reftype])
        db_session.flush()

        req.json_body = {
            'site': site_la.id,
            'references': [
                {'reference_type': reftype.id,
                 'reference_number': u'ABC'}
            ]
        }

        # Fake generate a PID, the roster should unit test this
        with mock.patch('occams_studies.views.patient.generate') as generate:
            generate.return_value = u'12345'
            res = self._call_fut(models.PatientFactory(req), req)

        assert generate.called
        assert check_csrf_token.called
        assert u'12345' == res['pid']
        assert site_la.id == res['site']['id']
        assert [(reftype.id, u'ABC')] == \
            [(r['reference_type']['id'], r['reference_number'])
             for r in res['references']]


class TestDeleteJson:

    def _call_fut(self, *args, **kw):
        from occams_studies.views.patient import delete_json as view
        return view(*args, **kw)

    def test_delete(self, req, db_session, check_csrf_token):
        """
        It should allow a valid principal to delete a patient
        """
        from collections import OrderedDict
        import mock
        from occams_studies import models

        site_la = models.Site(name=u'la', title=u'LA')
        patient = models.Patient(site=site_la, pid=u'12345')
        db_session.add(patient)
        db_session.flush()
        patient_id = patient.id

        req.session['viewed'] = OrderedDict([('12345', {})])
        req.session.changed = mock.Mock()
        self._call_fut(patient, req)

        assert db_session.query(models.Patient).get(patient_id) is None
        assert u'12345' not in req.session['viewed']

    def test_cascade_entities(self, req, db_session, check_csrf_token):
        """
        It should delete associated entities
        """

        from datetime import date
        from occams_datastore import models as datastore
        from occams_studies import models

        schema = datastore.Schema(
            name=u'somepatientform',
            title=u'Some Patient Form',
            publish_date=date.today())
        entity = datastore.Entity(
            collect_date=date.today(),
            schema=schema)
        patient = models.Patient(
            site=models.Site(name=u'la', title=u'LA'),
            pid=u'12345')
        patient.entities.add(entity)
        db_session.add_all([patient, entity, schema])
        db_session.flush()

        patient = db_session.query(models.Patient).one()

        self._call_fut(patient, req)

        assert 0 == db_session.query(datastore.Entity).count()
