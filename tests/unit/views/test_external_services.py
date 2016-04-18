import pytest


@pytest.yield_fixture
def check_csrf_token(config):
    import mock
    name = 'occams_studies.views.study.check_csrf_token'
    with mock.patch(name) as patch:
        yield patch


class TestExternalServiceView:

    def _call_fut(self, *args, **kw):
        from occams_studies.views.external_service import view

        return view(*args, **kw)

    def test_view(self, req, db_session, factories):
        """
        It should render the external services main view page with a study obj
        """
        from occams_studies import models
        from webob.multidict import MultiDict

        study = factories.StudyFactory.create()
        cycle = factories.CycleFactory.create(
            study=study
        )
        cycle.__parent__ = study

        db_session.flush()

        req.GET = MultiDict([])
        res = self._call_fut(cycle, req)

        assert isinstance(res['study'], models.Study) is True


class TestExternalServiceList:

    def _call_fut(self, *args, **kw):
        from occams_studies.views.external_service import list_ as view

        return view(*args, **kw)

    def test_list(self, req, db_session, factories):
        """
        It should return a list of external services JSON records
        """
        from webob.multidict import MultiDict

        study = factories.StudyFactory.create()
        cycle = factories.CycleFactory.create(
            study=study
        )
        cycle.__parent__ = study

        factories.ExternalServiceFactory.create(
            study=study,
            title=u'test-service'
        )

        db_session.flush()

        req.GET = MultiDict([])
        res = self._call_fut(cycle, req)

        assert res['external_services'][0]['title'] == u'test-service'
        assert len(res['external_services']) == 1


class TestExternalServiceViewJSON:

    def _call_fut(self, *args, **kw):
        from occams_studies.views.external_service import view_json as view

        return view(*args, **kw)

    def test_view_json(self, req, db_session, factories):
        """
        It should return a single JSON record for the study's external service
        """
        from webob.multidict import MultiDict

        study = factories.StudyFactory.create()

        external_service = factories.ExternalServiceFactory.create(
            study=study,
            title=u'test-service'
        )

        db_session.flush()

        req.GET = MultiDict([])
        res = self._call_fut(external_service, req)

        assert res['title'] == u'test-service'


class TestDeleteJSON:

    def _call_fut(self, *args, **kw):
        from occams_studies.views.external_service import delete_json as view

        return view(*args, **kw)

    def test_delete_json(self, req, db_session, factories):
        """
        It should return a single JSON record for the study's external service
        """
        from webob.multidict import MultiDict

        from occams_studies import models

        study = factories.StudyFactory.create()

        external_service = factories.ExternalServiceFactory.create(
            study=study,
            title=u'test-service'
        )

        db_session.flush()

        req.GET = MultiDict([])
        self._call_fut(external_service, req)

        assert db_session.query(
            models.ExternalService).get(external_service.id) is None
        assert 0 == db_session.query(models.ExternalService).count()


class TestAddEditJSON:

    def _call_fut(self, *args, **kw):
        from occams_studies.views.external_service import edit_json as view

        return view(*args, **kw)

    def test_add_json(self, req, db_session, factories):
        """
        It should redirect to the new record details and add service to the
        db.
        """
        from webob.multidict import MultiDict

        from occams_studies import models

        study = factories.StudyFactory.create()

        external_service = factories.ExternalServiceFactory.create(
            study=study,
            title=u'test-service'
        )

        db_session.flush()

        payload = {
            'title': u'title',
            'description': u'test_description',
            'url_template': u'https://my_app/location?pid=${pid}'
        }

        req.method = 'POST'
        req.json_body = payload

        req.POST = MultiDict([])
        res = self._call_fut(external_service, req)

        service = (
            db_session.query(models.ExternalService)
            .filter_by(name=u'title')
        ).one()

        assert service.name == u'title'
        assert res.status_code == 303

    def test_add_json_w_errors(self, req, db_session, factories):
        """
        It should return status 400 and a json with validation errors.
        """
        from webob.multidict import MultiDict

        study = factories.StudyFactory.create()

        factories.ExternalServiceFactory.create(
            study=study,
            title=u'test-service'
        )

        db_session.flush()

        payload = {
            'description': u'test_description',
            'url_template': u'https://my_app/location?pid=${pid}'
        }

        req.method = 'POST'
        req.json_body = payload

        req.POST = MultiDict([])
        res = self._call_fut(study, req)

        assert res.status_code == 400
        assert res.json['errors']['title'] == u'This field is required.'

    def test_add_json_w_duplicate_service_exists(self, req, db_session, factories):
        """
        It should return status 400 and an error indicating a service
        with this name exists.
        """
        from webob.multidict import MultiDict

        study = factories.StudyFactory.create()

        factories.ExternalServiceFactory.create(
            study=study,
            name=u'test-service',
            title=u'test-service'
        )

        db_session.flush()

        payload = {
            'title': u'test-service',
            'description': u'test-description',
            'url_template': u'https://my_app/location?pid=${pid}'
        }

        req.method = 'POST'
        req.json_body = payload

        req.POST = MultiDict([])
        res = self._call_fut(study, req)

        assert res.status_code == 400
        msg = u'Another external service with this name exists.'
        assert res.json['errors']['title'] == msg


    def test_edit_json(self, req, db_session, factories):
        """
        It should edit an external service.
        """
        from webob.multidict import MultiDict

        from occams_studies import models

        study = factories.StudyFactory.create()

        external_service = factories.ExternalServiceFactory.create(
            study=study,
            name=u'test-service',
            title=u'test-service'
        )

        db_session.flush()

        payload = {
            'title': u'test-service_altered',
            'description': u'test-description',
            'url_template': u'https://my_app/location?pid=${pid}'
        }

        req.method = 'PUT'
        req.json_body = payload

        req.PUT = MultiDict([])
        self._call_fut(external_service, req)

        service = (
            db_session.query(models.ExternalService)
        ).one()

        assert service.name == 'test-service-altered'
