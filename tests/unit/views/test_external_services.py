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

        external_service = factories.ExternalServiceFactory.create(
            study=study,
            title=u'test_service'
        )

        db_session.flush()

        req.GET = MultiDict([])
        res = self._call_fut(cycle, req)

        assert res['external_services'][0]['title'] == u'test_service'
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
            title=u'test_service'
        )

        db_session.flush()

        req.GET = MultiDict([])
        res = self._call_fut(external_service, req)

        assert res['title'] == u'test_service'


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
            title=u'test_service'
        )

        db_session.flush()

        req.GET = MultiDict([])
        res = self._call_fut(external_service, req)

        assert db_session.query(
            models.ExternalService).get(external_service.id) is None
        assert 0 == db_session.query(models.ExternalService).count()


class TestEditJSON:

    def _call_fut(self, *args, **kw):
        from occams_studies.views.external_service import edit_json as view

        return view(*args, **kw)

    def test_edit_json(self, req, db_session, factories):
        """
        It should redirect to the new record details
        """
        from webob.multidict import MultiDict

        from occams_studies import models

        study = factories.StudyFactory.create()

        external_service = factories.ExternalServiceFactory.create(
            study=study,
            title=u'test_service'
        )

        db_session.flush()

        payload = {
            'title': 'test_title',
            'name': 'test_name',
            'description': 'test_description',
            'url_template': 'https://my_app/location?pid=${pid}'
        }

        req.json_body = payload

        req.GET = MultiDict([])
        res = self._call_fut(external_service, req)

        from pytest import set_trace; set_trace()

        # assert db_session.query(
        #     models.ExternalService).get(external_service.id) is None
        # assert 0 == db_session.query(models.ExternalService).count()
