import mock

from tests import IntegrationFixture


@mock.patch('occams.studies.views.study.check_csrf_token')
class TestEditJson(IntegrationFixture):

    def call_view(self, context, request):
        from occams.studies.views.study import edit_json as view
        return view(context, request)

    def test_add(self, check_csrf_token):
        """
        It should be able to add a new study
        """
        from datetime import date
        from pyramid import testing
        from occams.studies import Session, models

        self.config.add_route('study', '/{study}')

        self.call_view(models.StudyFactory(None), testing.DummyRequest(
            json_body={
                'name': u'somestudy',
                'title': u'Some study',
                'short_title': u'sfstudy',
                'code': u'111',
                'consent_date': str(date.today())}))

        self.assertIsNotNone(
            Session.query(models.Study).filter_by(name='somestudy').first())

    def test_enforce_unique_name(self, check_csrf_token):
        """
        It should make sure the name stays unique when adding new studies
        """
        from datetime import date
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams.studies import models, Session

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today())

        Session.add_all([study])
        Session.flush()

        with self.assertRaises(HTTPBadRequest) as cm:
            self.call_view(models.StudyFactory(None), testing.DummyRequest(
                json_body={
                    'name': 'somestudy',
                    'title': 'Should fail',
                    'short_title': 'sfstudy',
                    'code': '111',
                    'consent_date': str(date.today())}))

        self.assertIn(
            'already exists',
            cm.exception.json['errors']['name'].lower())

    def test_edit_unique_name(self, check_csrf_token):
        """
        It should allow the study to be able to change its unique name
        """
        from datetime import date
        from pyramid import testing
        from occams.studies import models, Session

        self.config.add_route('study', '/{study}')

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today())

        Session.add_all([study])
        Session.flush()
        response = self.call_view(study, testing.DummyRequest(
            json_body={
                'name': 'newname',
                'title': study.title,
                'short_title': study.short_title,
                'code': study.code,
                'consent_date': str(study.consent_date)}))

        self.assertIsNotNone(response)


@mock.patch('occams.studies.views.study.check_csrf_token')
class TestDeleteJson(IntegrationFixture):

    def call_view(self, context, request):
        from occams.studies.views.study import delete_json as view
        return view(context, request)

    def test_no_enrollments(self, check_csrf_token):
        """
        It should allow deleting of a study if it has no enrollments
        """

        from datetime import date
        from pyramid import testing
        from occams.studies import models, Session

        self.config.add_route('studies', '/')

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today())

        Session.add_all([study])
        Session.flush()

        self.call_view(study, testing.DummyRequest())
        self.assertEqual(0, Session.query(models.Study).count())

    def test_has_enrollments(self, check_csrf_token):
        """
        It should not allow deletion of a study if it has enrollments
        (unless administrator)
        """
        from datetime import date
        from pyramid import testing
        from pyramid.httpexceptions import HTTPForbidden
        from occams.studies import models, Session

        self.config.add_route('studies', '/')

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today())

        enrollment = models.Enrollment(
            study=study,
            consent_date=date.today(),
            patient=models.Patient(
                site=models.Site(name='ucsd', title=u'UCSD'),
                pid=u'12345'))

        Session.add_all([study, enrollment])
        Session.flush()

        # Should not be able to delete if not an admin
        self.config.testing_securitypolicy(permissive=False)
        with self.assertRaises(HTTPForbidden):
            self.call_view(study, testing.DummyRequest())

        self.config.testing_securitypolicy(permissive=True)
        self.call_view(study, testing.DummyRequest())
        self.assertEqual(0, Session.query(models.Study).count())


@mock.patch('occams.studies.views.study.check_csrf_token')
class TestAddSchemaJson(IntegrationFixture):

    def call_view(self, context, request):
        from occams.studies.views.study import add_schema_json as view
        return view(context, request)

    def test_basic(self, check_csrf_token):
        """
        It should allow adding a schema to a study
        """
        from datetime import date
        from pyramid import testing
        from occams.studies import models, Session

        schema = models.Schema(
            name='test', title=u'', publish_date=date.today())

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today())

        Session.add_all([study, schema])
        Session.flush()

        self.call_view(study, testing.DummyRequest(
            json_body={'schema': schema.name, 'versions': [schema.id]}))

        self.assertIn(schema, study.schemata)

    def test_update_cycles(self, check_csrf_token):
        """
        It should also update cycle versions
        """
        from datetime import date, timedelta
        from pyramid import testing
        from occams.studies import models, Session

        today = date.today()
        tomorrow = today + timedelta(days=1)

        v1 = models.Schema(name=u'test', title=u'', publish_date=today)
        v2 = models.Schema(name=u'test', title=u'', publish_date=tomorrow)

        cycle = models.Cycle(
            name=u'wk-001', title=u'WK-001', schemata=set([v1]))

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            cycles=[cycle],
            schemata=set([v1]),
            consent_date=date.today())

        Session.add_all([study, v1, v2])
        Session.flush()

        self.call_view(study, testing.DummyRequest(
            json_body={'schema': v1.name, 'versions': [v2.id]}))

        self.assertIn(v2, study.schemata)
        # v2 should have been passed on to the cycle using it as well
        self.assertIn(v2, cycle.schemata)

    def test_fail_if_not_published(self, check_csrf_token):
        """
        It should fail if the schema is not published
        """
        from datetime import date
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams.studies import models, Session

        schema = models.Schema(name='test', title=u'')

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today())

        Session.add_all([study, schema])
        Session.flush()

        Session.execute(
            models.patient_schema_table
            .insert()
            .values({'schema_id': schema.id}))

        with self.assertRaises(HTTPBadRequest) as cm:
            self.call_view(study, testing.DummyRequest(
                json_body={'schema': schema.name, 'versions': [schema.id]}))

        self.assertIn(
            'not published',
            cm.exception.json['errors']['versions-0'])

    def test_fail_if_not_same_schema(self, check_csrf_token):
        """
        It should fail if the schema and versions do not match
        """
        from datetime import date
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams.studies import models, Session

        schema = models.Schema(
            name='test', title=u'', publish_date=date.today())

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today())

        Session.add_all([study, schema])
        Session.flush()

        with self.assertRaises(HTTPBadRequest) as cm:
            self.call_view(study, testing.DummyRequest(
                json_body={'schema': 'otherform', 'versions': [schema.id]}))

        self.assertIn(
            'Incorrect versions',
            cm.exception.json['errors']['versions-0'])

    def test_fail_if_patient_schema(self, check_csrf_token):
        """
        It should not allow patient schemata to be used as study schemata
        """
        from datetime import date
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams.studies import models, Session

        schema = models.Schema(
            name='test', title=u'', publish_date=date.today())

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today())

        Session.add_all([study, schema])
        Session.flush()

        Session.execute(
            models.patient_schema_table
            .insert()
            .values({'schema_id': schema.id}))

        with self.assertRaises(HTTPBadRequest) as cm:
            self.call_view(study, testing.DummyRequest(
                json_body={'schema': schema.name, 'versions': [schema.id]}))

        self.assertIn(
            'already a patient form',
            cm.exception.json['errors']['schema'].lower())

    def test_fail_if_randomization_schema(self, check_csrf_token):
        """
        It should not allow randomization schemata to be used as study schemata
        """
        from datetime import date
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams.studies import models, Session

        schema = models.Schema(
            name='test', title=u'', publish_date=date.today())

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today(),
            is_randomized=True,
            randomization_schema=schema)

        Session.add_all([study, schema])
        Session.flush()

        with self.assertRaises(HTTPBadRequest) as cm:
            self.call_view(study, testing.DummyRequest(
                json_body={'schema': schema.name, 'versions': [schema.id]}))

        self.assertIn(
            'already a randomization form',
            cm.exception.json['errors']['schema'].lower())

    def test_fail_if_termination_schema(self, check_csrf_token):
        """
        It should not allow termination  schemata to be used as study schemata
        """
        from datetime import date
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams.studies import models, Session

        schema = models.Schema(
            name='test', title=u'', publish_date=date.today())

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today(),
            termination_schema=schema)

        Session.add_all([study, schema])
        Session.flush()

        with self.assertRaises(HTTPBadRequest) as cm:
            self.call_view(study, testing.DummyRequest(
                json_body={'schema': schema.name, 'versions': [schema.id]}))

        self.assertIn(
            'already a termination form',
            cm.exception.json['errors']['schema'].lower())


@mock.patch('occams.studies.views.study.check_csrf_token')
class TestDeleteSchemaJson(IntegrationFixture):

    def call_view(self, context, request):
        from occams.studies.views.study import delete_schema_json as view
        return view(context, request)

    def test_success(self, check_csrf_token):
        """
        It should remove the schema from the study and cascade to its cycles
        """
        from datetime import date
        from pyramid import testing
        from occams.studies import models, Session

        schema = models.Schema(
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
            start_date=date.today(),
            consent_date=date.today(),
            cycles=[cycle],
            schemata=set([schema]))

        Session.add_all([study, schema])
        Session.flush()

        self.call_view(study, testing.DummyRequest(
            matchdict={'schema': schema.name}))

        self.assertNotIn(schema, study.schemata)
        self.assertNotIn(schema, cycle.schemata)

    def test_not_found(self, check_csrf_token):
        """
        It should fail if the schema specified does not exist
        """
        from datetime import date
        from pyramid import testing
        from pyramid.httpexceptions import HTTPNotFound
        from occams.studies import models, Session

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today())

        Session.add_all([study])
        Session.flush()

        with self.assertRaises(HTTPNotFound):
            self.call_view(study, testing.DummyRequest(
                matchdict={'schema': 'idonotexist'}))


@mock.patch('occams.studies.views.study.check_csrf_token')
class TestEditScheduleJson(IntegrationFixture):

    def call_view(self, context, request):
        from occams.studies.views.study import edit_schedule_json as view
        return view(context, request)

    def test_schema_in_study(self, check_csrf_tokne):
        """
        It should fail if the schema is not part of the study
        """
        from datetime import date
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams.studies import models, Session

        schema = models.Schema(
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
            start_date=date.today(),
            consent_date=date.today(),
            cycles=[cycle])

        Session.add_all([study, schema])
        Session.flush()

        with self.assertRaises(HTTPBadRequest) as cm:
            self.call_view(study, testing.DummyRequest(
                json_body={
                    'schema': schema.name,
                    'cycle': cycle.id,
                    'enabled': True}))

        self.assertIn(
            'not a valid choice',
            cm.exception.json['errors']['schema'].lower())

    def test_cycle_in_study(self, check_csrf_token):
        """
        It should fail if the cycle is not part of the study
        """
        from datetime import date
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams.studies import models, Session

        schema = models.Schema(
            name='test', title=u'Test', publish_date=date.today())

        other_cycle = models.Cycle(name=u'week-1', title=u'Title', week=1)

        other_study = models.Study(
            name=u'otherstudy',
            title=u'Other Study',
            short_title=u'ostudy',
            code=u'111',
            start_date=date.today(),
            consent_date=date.today(),
            cycles=[other_cycle])

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today(),
            schemata=set([schema]))

        Session.add_all([study, schema, other_study])
        Session.flush()

        with self.assertRaises(HTTPBadRequest) as cm:
            self.call_view(study, testing.DummyRequest(
                json_body={
                    'schema': schema.name,
                    'cycle': other_cycle.id,
                    'enabled': True}))

        self.assertIn(
            'not a valid choice',
            cm.exception.json['errors']['cycle'].lower())

    def test_enable(self, check_csrf_token):
        """
        It should successfully add a schema to a cycle
        """
        from datetime import date
        from pyramid import testing
        from occams.studies import models, Session

        schema = models.Schema(
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
            start_date=date.today(),
            consent_date=date.today(),
            cycles=[cycle],
            schemata=set([schema]))

        Session.add_all([study, schema])
        Session.flush()

        self.call_view(study, testing.DummyRequest(
            json_body={
                'schema': schema.name,
                'cycle': cycle.id,
                'enabled': True}))

        self.assertIn(schema, cycle.schemata)

    def test_disable(self, check_csrf_token):
        """
        It should successfully disable schema from a cycle
        """
        from datetime import date
        from pyramid import testing
        from occams.studies import models, Session

        schema = models.Schema(
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
            start_date=date.today(),
            consent_date=date.today(),
            cycles=[cycle],
            schemata=set([schema]))

        Session.add_all([study, schema])
        Session.flush()

        self.call_view(study, testing.DummyRequest(
            json_body={
                'schema': schema.name,
                'cycle': cycle.id,
                'enabled': False}))

        self.assertNotIn(schema, cycle.schemata)


@mock.patch('occams.studies.views.study.check_csrf_token')
class TestAvailableSchemata(IntegrationFixture):

    def call_view(self, context, request):
        from occams.studies.views.study import available_schemata as view
        return view(context, request)

    def test_no_params(self, check_csrf_token):
        """
        It should just return all schemata if there is not study context
        """
        from datetime import date
        from pyramid import testing
        from webob.multidict import MultiDict
        from occams.studies import models, Session

        Session.add_all([
            models.Schema(name='v', title=u'V', publish_date=date.today())])
        Session.flush()

        request = testing.DummyRequest(params=MultiDict())
        result = self.call_view(models.StudyFactory(request), request)
        self.assertEqual('v', result['schemata'][0]['name'])

    def test_term(self, check_csrf_token):
        """
        It should filter schemata by title or publish_date
        """
        from datetime import date
        from pyramid import testing
        from webob.multidict import MultiDict
        from occams.studies import models, Session

        Session.add_all([
            models.Schema(name='v', title=u'V', publish_date=date.today()),
            models.Schema(name='xyz', title=u'XYZ', publish_date=date.today())
            ])
        Session.flush()

        request = testing.DummyRequest(params=MultiDict([('term', 'x')]))
        result = self.call_view(models.StudyFactory(request), request)
        self.assertEqual('xyz', result['schemata'][0]['name'])

    def test_schema(self, check_csrf_token):
        """
        It should just return all publish_dates for the specific "schema"
        """
        from datetime import date, timedelta
        from pyramid import testing
        from webob.multidict import MultiDict
        from occams.studies import models, Session

        today = date.today()
        tomorrow = date.today() + timedelta(days=1)

        Session.add_all([
            models.Schema(name='v', title=u'V', publish_date=today),
            models.Schema(name='v', title=u'V', publish_date=tomorrow),
            models.Schema(name='x', title=u'x', publish_date=today)])
        Session.flush()

        request = testing.DummyRequest(params=MultiDict([('schema', 'v')]))
        result = self.call_view(models.StudyFactory(request), request)
        self.assertEqual(2, len(result['schemata']))

    def test_exclude_randomization(self, check_csrf_token):
        """
        It should exlude randomization forms used by the study (editing)
        """
        from datetime import date
        from pyramid import testing
        from webob.multidict import MultiDict
        from occams.studies import models, Session

        x = models.Schema(name='x', title=u'x', publish_date=date.today())
        y = models.Schema(name='y', title=u'Y', publish_date=date.today())

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today(),
            is_randomized=True,
            randomization_schema=x)

        Session.add_all([x, y, study])
        Session.flush()

        request = testing.DummyRequest(params=MultiDict())
        result = self.call_view(study, request)
        self.assertEqual(1, len(result['schemata']))
        self.assertEqual('y', result['schemata'][0]['name'])

    def test_exclude_termination(self, check_csrf_token):
        """
        It should exlude termination forms used by the study (editing)
        """
        from datetime import date
        from pyramid import testing
        from webob.multidict import MultiDict
        from occams.studies import models, Session

        x = models.Schema(name='x', title=u'x', publish_date=date.today())
        y = models.Schema(name='y', title=u'Y', publish_date=date.today())

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today(),
            termination_schema=x)

        Session.add_all([x, y, study])
        Session.flush()

        request = testing.DummyRequest(params=MultiDict())
        result = self.call_view(study, request)
        self.assertEqual(1, len(result['schemata']))
        self.assertEqual('y', result['schemata'][0]['name'])

    def test_exclude_schema(self, check_csrf_token):
        """
        It should exlude general forms used by the study (editing)
        """
        from datetime import date
        from pyramid import testing
        from webob.multidict import MultiDict
        from occams.studies import models, Session

        x = models.Schema(name='x', title=u'x', publish_date=date.today())
        y = models.Schema(name='y', title=u'Y', publish_date=date.today())

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today(),
            schemata=set([x]))

        Session.add_all([x, y, study])
        Session.flush()

        request = testing.DummyRequest(params=MultiDict())
        result = self.call_view(study, request)
        self.assertEqual(1, len(result['schemata']))
        self.assertEqual('y', result['schemata'][0]['name'])


@mock.patch('occams.studies.views.study.check_csrf_token')
class TestUploadRandomizationJson(IntegrationFixture):

    def call_view(self, context, request):
        from occams.studies.views.study import \
            upload_randomization_json as view
        return view(context, request)

    def test_not_randomized(self, check_csrf_token):
        """
        It should only allow uploads if the study is randomized
        """

        from datetime import date
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams.studies import models, Session

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            consent_date=date.today())

        Session.add(study)
        Session.flush()

        with self.assertRaises(HTTPBadRequest) as cm:
            self.call_view(study, testing.DummyRequest())

        self.assertTrue(check_csrf_token.called)
        self.assertIn('not randomized', cm.exception.body)

    def test_valid_csv(self, check_csrf_token):
        """
        It should only accept CSV files
        """
        import tempfile
        from datetime import date
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams.studies import models, Session

        schema = models.Schema(
            name='rand', title=u'Rand', publish_date=date.today())

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            is_randomized=True,
            randomization_schema=schema,
            consent_date=date.today())

        Session.add(study)
        Session.flush()

        class DummyUpload:
            pass

        with tempfile.NamedTemporaryFile(prefix='nose-', suffix='.exe') as fp:
            upload = DummyUpload()
            upload.file = fp
            upload.filename = fp.name

            with self.assertRaises(HTTPBadRequest) as cm:
                self.call_view(study, testing.DummyRequest(
                    post={'upload': upload}))

            self.assertTrue(check_csrf_token.called)
            self.assertIn('must be CSV', cm.exception.body)

    def test_incomplete_header(self, check_csrf_token):
        """
        It should include randomization schema attribute names in the header
        """
        import tempfile
        import csv
        from datetime import date
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams.studies import models, Session

        schema = models.Schema(
            name='rand', title=u'Rand', publish_date=date.today(),
            attributes={
                'criteria': models.Attribute(
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

        Session.add(study)
        Session.flush()

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

            with self.assertRaises(HTTPBadRequest) as cm:
                self.call_view(study, testing.DummyRequest(
                    post={'upload': upload}))

            self.assertTrue(check_csrf_token.called)
            self.assertIn('missing', cm.exception.body)

    def test_valid_upload(self, check_csrf_token):
        """
        It should be able to upload a perfectly valid CSV
        """
        import tempfile
        import csv
        from datetime import date
        from pyramid import testing
        from occams.studies import models, Session

        schema = models.Schema(
            name='rand', title=u'Rand', publish_date=date.today(),
            attributes={
                'criteria': models.Attribute(
                    name='criteria',
                    title=u'Criteria',
                    type='string',
                    order=0)})

        state = models.State(name='complete', title=u'Complete')

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            is_randomized=True,
            randomization_schema=schema,
            consent_date=date.today())

        Session.add_all([study, state])
        Session.flush()

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

            self.call_view(study, testing.DummyRequest(
                post={'upload': upload}))

            stratum = Session.query(models.Stratum).one()
            entity = Session.query(models.Entity).one()
            self.assertEquals(stratum.arm.name, 'UCSD')
            self.assertIn(entity, stratum.entities)
            self.assertEquals(entity['criteria'], 'is smart')

    def test_duplicate_rids(self, check_csrf_token):
        """
        It should fail if the upload contains repeated rids
        """
        import tempfile
        import csv
        from datetime import date
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams.studies import models, Session

        schema = models.Schema(
            name='rand', title=u'Rand', publish_date=date.today(),
            attributes={
                'criteria': models.Attribute(
                    name='criteria',
                    title=u'Criteria',
                    type='string',
                    order=0)})

        state = models.State(name='complete', title=u'Complete')

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            is_randomized=True,
            randomization_schema=schema,
            consent_date=date.today())

        Session.add_all([study, state])
        Session.flush()

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

            self.call_view(study, testing.DummyRequest(
                post={'upload': upload}))

            fp.seek(0)

            with self.assertRaises(HTTPBadRequest) as cm:
                self.call_view(study, testing.DummyRequest(
                    post={'upload': upload}))

            self.assertIn('existing reference numbers', cm.exception.body)
