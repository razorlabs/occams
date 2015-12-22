import pytest


@pytest.yield_fixture
def check_csrf_token(config):
    import mock
    name = 'occams_studies.views.study.check_csrf_token'
    with mock.patch(name) as patch:
        yield patch


class TestCyclesJson:

    def _call_fut(self, *args, **kw):
        from occams_studies.views.visit import cycles_json as view
        return view(*args, **kw)

    def test_by_query(self, req, db_session,):
        """
        It should allow fetching via search terms (typical use)
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

        cycle1 = models.Cycle(name='week-1', title=u'Foo Week 1', week=1)
        cycle2 = models.Cycle(name='week-2', title=u'Bar Week 2', week=2)

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        study.cycles.append(cycle1)
        study.cycles.append(cycle2)

        db_session.add_all([patient, study])
        db_session.flush()

        req.GET = MultiDict([('q', u'foo')])
        res = self._call_fut(patient['visits'], req)

        assert cycle1.id == res['cycles'][0]['id']

    def test_by_ids(self, req, db_session,):
        """
        It should allow search via direct ids (for pre-entered values)
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

        cycle1 = models.Cycle(name='week-1', title=u'Foo Week 1', week=1)
        cycle2 = models.Cycle(name='week-2', title=u'Bar Week 2', week=2)

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        study.cycles.append(cycle1)
        study.cycles.append(cycle2)

        db_session.add_all([patient, study])
        db_session.flush()

        req.GET = MultiDict([('ids', cycle1.id)])
        res = self._call_fut(patient['visits'], req)

        assert cycle1.id == res['cycles'][0]['id']


class TestValidateCycles:

    def _call_fut(self, *args, **kw):
        from occams_studies.views.visit import validate_cycles as view
        return view(*args, **kw)

    def test_call_success(self, req, db_session,):
        """
        It should be able to validate cycles via GET (for AJAX req)
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

        cycle1 = models.Cycle(name='week-1', title=u'Foo Week 1', week=1)
        cycle2 = models.Cycle(name='week-2', title=u'Bar Week 2', week=2)

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        study.cycles.append(cycle1)
        study.cycles.append(cycle2)

        db_session.add_all([patient, study])
        db_session.flush()

        req.GET = MultiDict([
            ('cycles', ','.join(map(str, [cycle1.id, cycle2.id])))])

        res = self._call_fut(patient['visits'], req)

        assert res

    def test_call_fail(self, req, db_session,):
        """
        It should return an validation error string if the cycles are invalid
        """
        from webob.multidict import MultiDict
        from occams_studies import models

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        db_session.add_all([patient])
        db_session.flush()

        req.GET = MultiDict([('cycles', '123')])
        res = self._call_fut(patient['visits'], req)
        assert 'not found' in res.lower()


class TestEditJson:

    def _call_fut(self, *args, **kw):
        from occams_studies.views.visit import edit_json as view
        return view(*args, **kw)

    def test_valid_cycle(self, req, db_session, check_csrf_token):
        """
        It should only allow existing cycles
        """
        from datetime import date
        from pyramid.httpexceptions import HTTPBadRequest
        from occams_studies import models

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        db_session.add_all([patient])
        db_session.flush()

        req.json_body = {
            'cycles': ['123'],
            'visit_date': str(date.today())
        }

        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(patient['visits'], req)

        assert 'not found' in \
            excinfo.value.json['errors']['cycles-0'].lower()

    def test_unique_cycle(self, req, db_session, check_csrf_token):
        """
        It should not allow repeat cycles (unless it's interim)
        """
        from datetime import date, timedelta
        from pyramid.httpexceptions import HTTPBadRequest
        from occams_studies import models

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            consent_date=date.today())

        cycle = models.Cycle(name='week-1', title=u'', week=1)

        study.cycles.append(cycle)

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        visit = models.Visit(
            patient=patient, cycles=[cycle], visit_date=date.today())

        db_session.add_all([patient, study, visit])
        db_session.flush()

        req.json_body = {
            'cycles': [cycle.id],
            'visit_date': str(date.today() + timedelta(days=1))
        }

        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(patient['visits'], req)

        assert 'already in use' in \
            excinfo.value.json['errors']['cycles-0'].lower()

        # The exception is interims
        cycle.is_interim = True
        db_session.flush()
        res = self._call_fut(patient['visits'], req)

        assert res is not None

    def test_unique_visit_date(self, req, db_session, check_csrf_token):
        """
        It should not allow duplicate visit dates
        """
        from datetime import date
        from pyramid.httpexceptions import HTTPBadRequest
        from occams_studies import models

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
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

        db_session.add_all([patient, study, visit])
        db_session.flush()

        req.json_body = {
            'cycles': [cycle2.id],
            'visit_date': str(date.today())
        }

        # Update the visit, should allow to update the date
        self._call_fut(visit, req)

        # New visits cannot share dates
        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(patient['visits'], req)

        assert 'already exists' in \
            excinfo.value.json['errors']['visit_date']

    def test_include_forms(self, req, db_session, check_csrf_token):
        """
        It should allow the user to create cycle forms
        """
        from datetime import date, timedelta
        from occams_studies import models

        form1 = models.Schema(
            name='form1', title=u'', publish_date=date.today())

        form2 = models.Schema(
            name='form2', title=u'', publish_date=date.today())

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
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

        db_session.add_all([patient, study])
        db_session.flush()

        req.json_body = {
            'cycles': [cycle1.id],
            'visit_date': str(date.today() + timedelta(days=1)),
            'include_forms': True
        }

        res = self._call_fut(patient['visits'], req)

        assert ['form1'] == \
            [e['schema']['name'] for e in res['entities']]

        contexts = db_session.query(models.Context).all()

        assert sorted(['patient', 'visit']) == \
            sorted([c.external for c in contexts])

        visit = db_session.query(models.Visit).get(res['id'])

        # Update to demonstrate forms can still be added on edit
        req.json_body = {
            'cycles': [cycle1.id, cycle2.id],
            'visit_date': str(date.today() + timedelta(days=1)),
            'include_forms': True
        }

        res = self._call_fut(visit, req)

        assert sorted(['form1', 'form2']) == \
            sorted([e['schema']['name'] for e in res['entities']])

        contexts = db_session.query(models.Context).all()

        assert sorted([(x, e['id'])
                       for e in res['entities']
                       for x in ('patient', 'visit')]) == \
            sorted([(c.external, c.entity_id) for c in contexts])

    def test_include_relative_form(self, req, db_session, check_csrf_token):
        """
        It should use the latest version of the form relative to the visit date
        """
        from datetime import date, timedelta
        from occams_studies import models

        t0 = date.today()
        t1 = t0 + timedelta(days=1)
        t2 = t1 + timedelta(days=1)

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            consent_date=date.today())

        cycle1 = models.Cycle(name='week-1', title=u'', week=1)
        cycle1.schemata.update([
            models.Schema(name='form1', title=u'', publish_date=t0),
            models.Schema(name='form1', title=u'', publish_date=t2)])
        study.cycles.append(cycle1)

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        db_session.add_all([patient, study])
        db_session.flush()

        req.json_body = {
            'cycles': [cycle1.id],
            'visit_date': str(t1),
            'include_forms': True
        }

        res = self._call_fut(patient['visits'], req)

        assert 1 == len(res['entities'])
        assert str(t0) == res['entities'][0]['schema']['publish_date']

    def test_include_not_retracted_form(
            self, req, db_session, check_csrf_token):
        """
        It should not use retracted forms, even if there are the most recent
        """
        from datetime import date, timedelta
        from occams_studies import models

        t0 = date.today()
        t1 = t0 + timedelta(days=1)
        t2 = t1 + timedelta(days=1)

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            consent_date=date.today())

        cycle1 = models.Cycle(name='week-1', title=u'', week=1)
        cycle1.schemata.update([
            models.Schema(name='form1', title=u'', publish_date=t0),
            models.Schema(name='form1', title=u'', publish_date=t2,
                          retract_date=t2)])
        study.cycles.append(cycle1)

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        db_session.add_all([patient, study])
        db_session.flush()

        req.json_body = {
            'cycles': [cycle1.id],
            'visit_date': str(t2),
            'include_forms': True
        }

        res = self._call_fut(patient['visits'], req)

        assert 1 == len(res['entities'])
        assert str(t0) == res['entities'][0]['schema']['publish_date']

    def test_update_patient(self, req, db_session, check_csrf_token):
        """
        It should also mark the patient as modified
        """
        from datetime import date
        from occams_studies import models

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            consent_date=date.today())

        cycle1 = models.Cycle(study=study, name='week-1', title=u'', week=1)

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        db_session.add_all([patient, study])
        db_session.flush()

        old_modify_date = patient.modify_date

        req.json_body = {
            'cycles': [str(cycle1.id)],
            'visit_date': str(date.today())
        }

        self._call_fut(patient['visits'], req)

        assert old_modify_date < patient.modify_date


class TestDeleteJson:

    def _call_fut(self, *args, **kw):
        from occams_studies.views.visit import delete_json as view
        return view(*args, **kw)

    def test_update_patient(self, req, db_session, check_csrf_token):
        """
        It should also mark the patient as modified
        """
        from datetime import date
        from occams_studies import models

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        visit = models.Visit(
            patient=patient,
            visit_date=date.today())

        db_session.add_all([patient, visit])
        db_session.flush()

        old_modify_date = patient.modify_date
        self._call_fut(visit, req)
        assert old_modify_date < patient.modify_date

    def test_cascade_forms(self, req, db_session, check_csrf_token):
        """
        It should remove all visit-associated forms.
        """
        from datetime import date
        from occams_studies import models

        schema = models.Schema(
            name=u'sample',
            title=u'Some Sample',
            publish_date=date.today())

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
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

        db_session.add_all([patient, enrollment, study, visit])
        db_session.flush()

        visit_id = visit.id

        self._call_fut(visit, req)

        assert db_session.query(models.Visit).get(visit_id) is None
        assert 0 == db_session.query(models.Entity).count()


class TestFormDeleteJson:

    def _call_fut(self, *args, **kw):
        from occams_studies.views.form import bulk_delete_json as view
        return view(*args, **kw)

    def test_success(self, req, db_session, check_csrf_token):
        """
        It should allow removal of entities from a visit.
        """
        from datetime import date, timedelta
        from pyramid.httpexceptions import HTTPOk
        from occams_studies import models

        cycle = models.Cycle(name='week-1', title=u'', week=1)

        schema = models.Schema(
            name=u'sample', title=u'', publish_date=date.today())

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            consent_date=date.today(),
            cycles=[cycle],
            schemata=set([schema]))

        site = models.Site(name=u'ucsd', title=u'UCSD')

        default_state = (
            db_session.query(models.State)
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

        db_session.add_all([visit_a, study])
        db_session.flush()

        req.json_body = {
            'forms': [entity_a_2.id, entity_a_3.id]
        }

        res = self._call_fut(visit_a['forms'], req)

        # refresh the session so we can get a correct listing
        db_session.expunge_all()
        visit_a = db_session.query(models.Visit).get(visit_a.id)

        assert isinstance(res, HTTPOk)
        assert sorted([e.id for e in [entity_a_1]]) == \
            sorted([e.id for e in visit_a.entities])
