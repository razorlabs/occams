import pytest


@pytest.yield_fixture
def check_csrf_token(config):
    import mock
    name = 'occams.views.study.check_csrf_token'
    with mock.patch(name) as patch:
        yield patch


class TestEditJson:

    def _call_fut(self, *args, **kw):
        from occams.views.study import edit_json as view
        return view(*args, **kw)

    def test_add(self, req, dbsession, check_csrf_token):
        """
        It should be able to add a new study
        """
        from datetime import date
        from occams import models

        req.json_body = {
            'title': u'Some study',
            'short_title': u'sfstudy',
            'code': u'111',
            'consent_date': str(date.today())
        }

        self._call_fut(models.StudyFactory(None), req)

        res = (
            dbsession.query(models.Study)
            .filter_by(name=u'some-study')
            .first())

        assert res is not None

    def test_enforce_unique_name(self, req, dbsession, check_csrf_token):
        """
        It should make sure the name stays unique when adding new studies
        """
        from datetime import date
        from pyramid.httpexceptions import HTTPBadRequest
        from occams import models

        study = models.Study(
            name='some-study',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            consent_date=date.today())

        dbsession.add_all([study])
        dbsession.flush()

        req.json_body = {
            'title': u'Some Study',
            'short_title': u'sfstudy',
            'code': u'111',
            'consent_date': str(date.today())
        }

        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(models.StudyFactory(None), req)

        assert 'Does not yield a unique URL.' in \
            excinfo.value.json['errors']['title']

    def test_edit_unique_name(self, req, dbsession, check_csrf_token):
        """
        It should allow the study to be able to change its unique name
        """
        from datetime import date
        from occams import models

        study = models.Study(
            name='some-study',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            consent_date=date.today())

        dbsession.add_all([study])
        dbsession.flush()

        req.json_body = {
            'title': u'New Study Title',
            'short_title': study.short_title,
            'code': study.code,
            'consent_date': str(study.consent_date)
        }

        res = self._call_fut(study, req)

        assert res is not None


class TestDeleteJson:

    def _call_fut(self, *args, **kw):
        from occams.views.study import delete_json as view
        return view(*args, **kw)

    def test_no_enrollments(self, req, dbsession, check_csrf_token):
        """
        It should allow deleting of a study if it has no enrollments
        """

        from datetime import date
        from occams import models

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            consent_date=date.today())

        dbsession.add_all([study])
        dbsession.flush()

        self._call_fut(study, req)
        assert 0 == dbsession.query(models.Study).count()

    def test_has_enrollments(self, req, dbsession, config, check_csrf_token):
        """
        It should not allow deletion of a study if it has enrollments
        (unless administrator)
        """
        from datetime import date
        from pyramid.httpexceptions import HTTPForbidden
        from occams import models

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            consent_date=date.today())

        enrollment = models.Enrollment(
            study=study,
            consent_date=date.today(),
            patient=models.Patient(
                site=models.Site(name='ucsd', title=u'UCSD'),
                pid=u'12345'))

        dbsession.add_all([study, enrollment])
        dbsession.flush()

        # Should not be able to delete if not an admin
        config.testing_securitypolicy(permissive=False)
        with pytest.raises(HTTPForbidden):
            self._call_fut(study, req)

        config.testing_securitypolicy(permissive=True)
        self._call_fut(study, req)
        assert 0 == dbsession.query(models.Study).count()


class TestAddSchemaJson:

    def _call_fut(self, *args, **kw):
        from occams.views.study import add_schema_json as view
        return view(*args, **kw)

    def test_basic(self, req, dbsession, check_csrf_token):
        """
        It should allow adding a schema to a study
        """
        from datetime import date
        from occams_datastore import models as datastore
        from occams import models

        schema = datastore.Schema(
            name='test', title=u'', publish_date=date.today())

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            consent_date=date.today())

        dbsession.add_all([study, schema])
        dbsession.flush()

        req.json_body = {'schema': schema.name, 'versions': [schema.id]}
        self._call_fut(study, req)

        assert schema in study.schemata

    def test_update_cycles(self, req, dbsession, check_csrf_token):
        """
        It should also update cycle versions
        """
        from datetime import date, timedelta
        from occams_datastore import models as datastore
        from occams import models

        today = date.today()
        tomorrow = today + timedelta(days=1)

        v1 = datastore.Schema(name=u'test', title=u'', publish_date=today)
        v2 = datastore.Schema(name=u'test', title=u'', publish_date=tomorrow)

        cycle = models.Cycle(
            name=u'wk-001', title=u'WK-001', schemata=set([v1]))

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            cycles=[cycle],
            schemata=set([v1]),
            consent_date=date.today())

        dbsession.add_all([study, v1, v2])
        dbsession.flush()

        req.json_body = {'schema': v1.name, 'versions': [v2.id]}
        self._call_fut(study, req)

        assert v2 in study.schemata
        # v2 should have been passed on to the cycle using it as well
        assert v2 in cycle.schemata

    def test_fail_if_not_published(self, req, dbsession, check_csrf_token):
        """
        It should fail if the schema is not published
        """
        from datetime import date
        from pyramid.httpexceptions import HTTPBadRequest
        from occams_datastore import models as datastore
        from occams import models

        schema = datastore.Schema(name='test', title=u'')

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            consent_date=date.today())

        dbsession.add_all([study, schema])
        dbsession.flush()

        dbsession.execute(
            models.patient_schema_table
            .insert()
            .values({'schema_id': schema.id}))

        req.json_body = {'schema': schema.name, 'versions': [schema.id]}
        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(study, req)

        assert 'not published' in \
            excinfo.value.json['errors']['versions-0']

    def test_fail_if_not_same_schema(self, req, dbsession, check_csrf_token):
        """
        It should fail if the schema and versions do not match
        """
        from datetime import date
        from pyramid.httpexceptions import HTTPBadRequest
        from occams_datastore import models as datastore
        from occams import models

        schema = datastore.Schema(
            name='test', title=u'', publish_date=date.today())

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            consent_date=date.today())

        dbsession.add_all([study, schema])
        dbsession.flush()

        req.json_body = {'schema': u'otherform', 'versions': [schema.id]}
        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(study, req)

        assert 'Incorrect versions' in \
            excinfo.value.json['errors']['versions']

    def test_fail_if_patient_schema(self, req, dbsession, check_csrf_token):
        """
        It should not allow patient schemata to be used as study schemata
        """
        from datetime import date
        from pyramid.httpexceptions import HTTPBadRequest
        from occams_datastore import models as datastore
        from occams import models

        schema = datastore.Schema(
            name='test', title=u'', publish_date=date.today())

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            consent_date=date.today())

        dbsession.add_all([study, schema])
        dbsession.flush()

        dbsession.execute(
            models.patient_schema_table
            .insert()
            .values({'schema_id': schema.id}))

        req.json_body = {'schema': schema.name, 'versions': [schema.id]}

        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(study, req)

        assert 'already a patient form' in \
            excinfo.value.json['errors']['schema'].lower()

    def test_fail_if_randomization_schema(
            self, req, dbsession, check_csrf_token):
        """
        It should not allow randomization schemata to be used as study schemata
        """
        from datetime import date
        from pyramid.httpexceptions import HTTPBadRequest
        from occams_datastore import models as datastore
        from occams import models

        schema = datastore.Schema(
            name='test', title=u'', publish_date=date.today())

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            consent_date=date.today(),
            is_randomized=True,
            randomization_schema=schema)

        dbsession.add_all([study, schema])
        dbsession.flush()

        req.json_body = {'schema': schema.name, 'versions': [schema.id]}

        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(study, req)

        assert 'already a randomization form' in \
            excinfo.value.json['errors']['schema'].lower()

    def test_fail_if_termination_schema(
            self, req, dbsession, check_csrf_token):
        """
        It should not allow termination  schemata to be used as study schemata
        """
        from datetime import date
        from pyramid.httpexceptions import HTTPBadRequest
        from occams_datastore import models as datastore
        from occams import models

        schema = datastore.Schema(
            name='test', title=u'', publish_date=date.today())

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            consent_date=date.today(),
            termination_schema=schema)

        dbsession.add_all([study, schema])
        dbsession.flush()

        req.json_body = {'schema': schema.name, 'versions': [schema.id]}
        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(study, req)

        assert 'already a termination form' in \
            excinfo.value.json['errors']['schema'].lower()


class TestDeleteSchemaJson:

    def _call_fut(self, *args, **kw):
        from occams.views.study import delete_schema_json as view
        return view(*args, **kw)

    def test_success(self, req, dbsession, check_csrf_token):
        """
        It should remove the schema from the study and cascade to its cycles
        """
        from datetime import date
        from occams_datastore import models as datastore
        from occams import models

        schema = datastore.Schema(
            name='test', title=u'', publish_date=date.today())

        cycle = models.Cycle(
            name='week-1',
            title=u'Week 1',
            week=1,
            schemata=set([schema]))

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            consent_date=date.today(),
            cycles=[cycle],
            schemata=set([schema]))

        dbsession.add_all([study, schema])
        dbsession.flush()

        req.matchdict = {'schema': schema.name}
        self._call_fut(study, req)

        assert schema not in study.schemata
        assert schema not in cycle.schemata

    def test_not_found(self, req, dbsession, check_csrf_token):
        """
        It should fail if the schema specified does not exist
        """
        from datetime import date
        from pyramid.httpexceptions import HTTPNotFound
        from occams import models

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            consent_date=date.today())

        dbsession.add_all([study])
        dbsession.flush()

        req.matchdict = {'schema': 'idonotexist'}
        with pytest.raises(HTTPNotFound):
            self._call_fut(study, req)


class TestEditScheduleJson:

    def _call_fut(self, *args, **kw):
        from occams.views.study import edit_schedule_json as view
        return view(*args, **kw)

    def test_schema_in_study(self, req, dbsession, check_csrf_token):
        """
        It should fail if the schema is not part of the study
        """
        from datetime import date
        from pyramid.httpexceptions import HTTPBadRequest
        from occams_datastore import models as datastore
        from occams import models

        schema = datastore.Schema(
            name='test', title=u'Test', publish_date=date.today())

        cycle = models.Cycle(
            name='week-1',
            title=u'Week 1',
            week=1)

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            consent_date=date.today(),
            cycles=[cycle])

        dbsession.add_all([study, schema])
        dbsession.flush()

        req.json_body = {
            'schema': schema.name,
            'cycle': cycle.id,
            'enabled': True
        }

        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(study, req)

        assert 'not a valid choice' in \
            excinfo.value.json['errors']['schema'].lower()

    def test_cycle_in_study(self, req, dbsession, check_csrf_token):
        """
        It should fail if the cycle is not part of the study
        """
        from datetime import date
        from pyramid.httpexceptions import HTTPBadRequest
        from occams_datastore import models as datastore
        from occams import models

        schema = datastore.Schema(
            name='test', title=u'Test', publish_date=date.today())

        other_cycle = models.Cycle(name=u'week-1', title=u'Title', week=1)

        other_study = models.Study(
            name=u'otherstudy',
            title=u'Other Study',
            short_title=u'ostudy',
            code=u'111',
            consent_date=date.today(),
            cycles=[other_cycle])

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            consent_date=date.today(),
            schemata=set([schema]))

        dbsession.add_all([study, schema, other_study])
        dbsession.flush()

        req.json_body = {
            'schema': schema.name,
            'cycle': other_cycle.id,
            'enabled': True
        }

        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(study, req)

        assert 'not a valid choice' in \
            excinfo.value.json['errors']['cycle'].lower()

    def test_enable(self, req, dbsession, check_csrf_token):
        """
        It should successfully add a schema to a cycle
        """
        from datetime import date
        from occams_datastore import models as datastore
        from occams import models

        schema = datastore.Schema(
            name='test', title=u'Test', publish_date=date.today())

        cycle = models.Cycle(
            name='week-1',
            title=u'Week 1',
            week=1)

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            consent_date=date.today(),
            cycles=[cycle],
            schemata=set([schema]))

        dbsession.add_all([study, schema])
        dbsession.flush()

        req.json_body = {
            'schema': schema.name,
            'cycle': cycle.id,
            'enabled': True
        }

        self._call_fut(study, req)

        assert schema in cycle.schemata

    def test_disable(self, req, dbsession, check_csrf_token):
        """
        It should successfully disable schema from a cycle
        """
        from datetime import date
        from occams_datastore import models as datastore
        from occams import models

        schema = datastore.Schema(
            name='test', title=u'Test', publish_date=date.today())

        cycle = models.Cycle(
            name='week-1',
            title=u'Week 1',
            week=1,
            schemata=set([schema]))

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            consent_date=date.today(),
            cycles=[cycle],
            schemata=set([schema]))

        dbsession.add_all([study, schema])
        dbsession.flush()

        req.json_body = {
            'schema': schema.name,
            'cycle': cycle.id,
            'enabled': False
        }

        self._call_fut(study, req)

        assert schema not in cycle.schemata


class TestAvailableSchemata:

    def _call_fut(self, *args, **kw):
        from occams.views.study import available_schemata as view
        return view(*args, **kw)

    def test_no_params(self, req, dbsession, check_csrf_token):
        """
        It should just return all schemata if there is not study context
        """
        from datetime import date
        from webob.multidict import MultiDict
        from occams_datastore import models as datastore
        from occams import models

        dbsession.add_all([
            datastore.Schema(name='v', title=u'V', publish_date=date.today())])
        dbsession.flush()

        req.GET = MultiDict()
        res = self._call_fut(models.StudyFactory(req), req)
        assert 'v' == res['schemata'][0]['name']

    def test_term(self, req, dbsession, check_csrf_token):
        """
        It should filter schemata by title or publish_date
        """
        from datetime import date
        from webob.multidict import MultiDict
        from occams_datastore import models as datastore
        from occams import models

        dbsession.add_all([
            datastore.Schema(name='v', title=u'V', publish_date=date.today()),
            datastore.Schema(
                name='xyz', title=u'XYZ', publish_date=date.today())
            ])
        dbsession.flush()

        req.GET = MultiDict([('term', 'x')])
        res = self._call_fut(models.StudyFactory(req), req)
        assert 'xyz' == res['schemata'][0]['name']

    def test_schema(self, req, dbsession, check_csrf_token):
        """
        It should just return all publish_dates for the specific "schema"
        """
        from datetime import date, timedelta
        from webob.multidict import MultiDict
        from occams_datastore import models as datastore
        from occams import models

        today = date.today()
        tomorrow = date.today() + timedelta(days=1)

        dbsession.add_all([
            datastore.Schema(name='v', title=u'V', publish_date=today),
            datastore.Schema(name='v', title=u'V', publish_date=tomorrow),
            datastore.Schema(name='x', title=u'x', publish_date=today)])
        dbsession.flush()

        req.GET = MultiDict([('schema', 'v')])
        res = self._call_fut(models.StudyFactory(req), req)
        assert 2 == len(res['schemata'])

    def test_exclude_randomization(self, req, dbsession, check_csrf_token):
        """
        It should exlude randomization forms used by the study (editing)
        """
        from datetime import date
        from webob.multidict import MultiDict
        from occams_datastore import models as datastore
        from occams import models

        x = datastore.Schema(name='x', title=u'x', publish_date=date.today())
        y = datastore.Schema(name='y', title=u'Y', publish_date=date.today())

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            consent_date=date.today(),
            is_randomized=True,
            randomization_schema=x)

        dbsession.add_all([x, y, study])
        dbsession.flush()

        req.GET = MultiDict()
        res = self._call_fut(study, req)
        assert 1 == len(res['schemata'])
        assert 'y' == res['schemata'][0]['name']

    def test_exclude_termination(self, req, dbsession, check_csrf_token):
        """
        It should exlude termination forms used by the study (editing)
        """
        from datetime import date
        from webob.multidict import MultiDict
        from occams_datastore import models as datastore
        from occams import models

        x = datastore.Schema(name='x', title=u'x', publish_date=date.today())
        y = datastore.Schema(name='y', title=u'Y', publish_date=date.today())

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            consent_date=date.today(),
            termination_schema=x)

        dbsession.add_all([x, y, study])
        dbsession.flush()

        req.GET = MultiDict()
        res = self._call_fut(study, req)
        assert 1 == len(res['schemata'])
        assert 'y' == res['schemata'][0]['name']

    def test_exclude_schema(self, req, dbsession, check_csrf_token):
        """
        It should exlude general forms used by the study (editing)
        """
        from datetime import date
        from webob.multidict import MultiDict
        from occams_datastore import models as datastore
        from occams import models

        x = datastore.Schema(name='x', title=u'x', publish_date=date.today())
        y = datastore.Schema(name='y', title=u'Y', publish_date=date.today())

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            consent_date=date.today(),
            schemata=set([x]))

        dbsession.add_all([x, y, study])
        dbsession.flush()

        req.GET = MultiDict()
        res = self._call_fut(study, req)
        assert 1 == len(res['schemata'])
        assert 'y' == res['schemata'][0]['name']

    def test_exclude_schema_used_versions(
            self, req, dbsession, check_csrf_token):
        """
        It should exclude general versions already used by the form (editing)
        """
        from datetime import date, timedelta
        from webob.multidict import MultiDict
        from occams_datastore import models as datastore
        from occams import models

        today = date.today()
        tomorrow = today + timedelta(days=1)

        y0 = datastore.Schema(name='y', title=u'Y', publish_date=today)
        y1 = datastore.Schema(name='y', title=u'Y', publish_date=tomorrow)

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            consent_date=date.today(),
            schemata=set([y0]))

        dbsession.add_all([y0, y1, study])
        dbsession.flush()

        req.GET = MultiDict()
        res = self._call_fut(study, req)
        assert 1 == len(res['schemata'])
        assert str(tomorrow) == res['schemata'][0]['publish_date']


class TestUploadRandomizationJson:

    def _call_fut(self, *args, **kw):
        from occams.views.study import \
            upload_randomization_json as view
        return view(*args, **kw)

    def test_not_randomized(self, req, dbsession, check_csrf_token):
        """
        It should only allow uploads if the study is randomized
        """

        from datetime import date
        from pyramid.httpexceptions import HTTPBadRequest
        from occams import models

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            consent_date=date.today())

        dbsession.add(study)
        dbsession.flush()

        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(study, req)

        assert check_csrf_token.called
        assert 'not randomized' in excinfo.value.body

    def test_valid_csv(self, req, dbsession, check_csrf_token):
        """
        It should only accept CSV files
        """
        import tempfile
        from datetime import date
        from pyramid.httpexceptions import HTTPBadRequest
        from occams_datastore import models as datastore
        from occams import models

        schema = datastore.Schema(
            name='rand', title=u'Rand', publish_date=date.today())

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            is_randomized=True,
            randomization_schema=schema,
            consent_date=date.today())

        dbsession.add(study)
        dbsession.flush()

        class DummyUpload:
            pass

        with tempfile.NamedTemporaryFile(prefix='nose-', suffix='.exe') as fp:
            upload = DummyUpload()
            upload.file = fp
            upload.filename = fp.name

            req.POST = {'upload': upload}
            with pytest.raises(HTTPBadRequest) as excinfo:
                self._call_fut(study, req)

            assert check_csrf_token.called
            assert 'must be CSV' in excinfo.value.body

    def test_incomplete_header(self, req, dbsession, check_csrf_token):
        """
        It should include randomization schema attribute names in the header
        """
        import tempfile
        import csv
        from datetime import date
        from pyramid.httpexceptions import HTTPBadRequest
        from occams_datastore import models as datastore
        from occams import models

        schema = datastore.Schema(
            name='rand', title=u'Rand', publish_date=date.today(),
            attributes={
                'criteria': datastore.Attribute(
                    name='criteria',
                    title=u'Criteria',
                    type='string',
                    order=0)})

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            is_randomized=True,
            randomization_schema=schema,
            consent_date=date.today())

        dbsession.add(study)
        dbsession.flush()

        class DummyUpload:
            pass

        with tempfile.NamedTemporaryFile(prefix='nose-', suffix='.exe') as fp:
            upload = DummyUpload()
            upload.file = fp
            upload.filename = fp.name

            # forget the schema keys
            writer = csv.writer(fp)
            writer.writerow(['ARM', 'STRATA', 'BLOCKID', 'RANDID'])
            fp.flush()

            with pytest.raises(HTTPBadRequest) as excinfo:
                req.POST = {'upload': upload}
                self._call_fut(study, req)

            assert check_csrf_token.called
            assert 'missing' in excinfo.value.body

    def test_valid_upload(self, req, dbsession, check_csrf_token):
        """
        It should be able to upload a perfectly valid CSV
        """
        import tempfile
        import csv
        from datetime import date
        from occams_datastore import models as datastore
        from occams import models

        schema = datastore.Schema(
            name='rand', title=u'Rand', publish_date=date.today(),
            attributes={
                'criteria': datastore.Attribute(
                    name='criteria',
                    title=u'Criteria',
                    type='string',
                    order=0)})

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            is_randomized=True,
            randomization_schema=schema,
            consent_date=date.today())

        dbsession.add_all([study])
        dbsession.flush()

        class DummyUpload:
            pass

        with tempfile.NamedTemporaryFile(prefix='nose-', suffix='.exe') as fp:
            upload = DummyUpload()
            upload.file = fp
            upload.filename = fp.name

            # forget the schema keys
            writer = csv.writer(fp)
            writer.writerow([u'ARM', u'STRATA', u'BLOCKID', u'RANDID', u'CRITERIA'])  # noqa
            writer.writerow([u'UCSD', u'hints', u'1234567', u'987654', u'is smart'])  # noqa
            fp.flush()

            req.POST = {'upload': upload}
            self._call_fut(study, req)

            stratum = dbsession.query(models.Stratum).one()
            entity = dbsession.query(datastore.Entity).one()
            assert stratum.arm.name == 'UCSD'
            assert entity in stratum.entities
            assert entity['criteria'] == 'is smart'

    def test_duplicate_rids(self, req, dbsession, check_csrf_token):
        """
        It should fail if the upload contains repeated rids
        """
        import tempfile
        import csv
        from datetime import date
        from pyramid.httpexceptions import HTTPBadRequest
        from occams_datastore import models as datastore
        from occams import models

        schema = datastore.Schema(
            name='rand', title=u'Rand', publish_date=date.today(),
            attributes={
                'criteria': datastore.Attribute(
                    name='criteria',
                    title=u'Criteria',
                    type='string',
                    order=0)})

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            is_randomized=True,
            randomization_schema=schema,
            consent_date=date.today())

        dbsession.add_all([study])
        dbsession.flush()

        class DummyUpload:
            pass

        with tempfile.NamedTemporaryFile(prefix='nose-', suffix='.exe') as fp:
            upload = DummyUpload()
            upload.file = fp
            upload.filename = fp.name

            # forget the schema keys
            writer = csv.writer(fp)
            writer.writerow([u'ARM', u'STRATA', u'BLOCKID', u'RANDID', u'CRITERIA'])  # noqa
            writer.writerow([u'UCSD', u'hints', u'1234567', u'987654', u'is smart'])  # noqa
            fp.flush()

            req.POST = {'upload': upload}
            self._call_fut(study, req)

            fp.seek(0)

            with pytest.raises(HTTPBadRequest) as excinfo:
                req.POST = {'upload': upload}
                self._call_fut(study, req)

            assert 'existing reference numbers' in excinfo.value.body
