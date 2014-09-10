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
                'name': 'somestudy',
                'title': 'Some study',
                'short_title': 'sfstudy',
                'code': '111',
                'consent_date': date.today()}))

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
                    'consent_date': date.today()}))

        self.assertHasStringLike(
            cm.exception.json['validation_errors'],
            'already exists')

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
                'consent_date': study.consent_date}))

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
            json_body={'schema': schema.id}))

        self.assertIn(schema, study.schemata)
