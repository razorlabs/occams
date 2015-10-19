import pytest


class TestEditJson:

    def _call_fut(self, *args, **kw):
        from occams_studies.views.cycle import edit_json as view
        return view(*args, **kw)

    def test_add(self, req, db_session):
        """
        It should be able to add a new cycle
        """
        from datetime import date
        from occams_studies import models

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today())

        db_session.add_all([study])
        db_session.flush()

        req.json_body = {
            'name': 'week-1',
            'title': u'Week 1',
            'week': 1
        }

        self._call_fut(study['cycles'], req)

        assert 1 == study.cycles.count()
        assert 'week-1' == study.cycles[0].name

    def test_enforce_unique_name(self, req, db_session):
        """
        It should make sure the name stays unique when adding new cycles
        """
        from datetime import date
        from pyramid.httpexceptions import HTTPBadRequest
        from occams_studies import models

        cycle = models.Cycle(name='week-1', title=u'Week 1', week=1)

        study = models.Study(
            name=u'some-study',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today(),
            cycles=[cycle])

        db_session.add_all([study])
        db_session.flush()

        req.json_body = {
            'title': u'Week 1',
            'week': 2
        }

        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(study['cycles'], req)

        assert 'not yield a unique' in \
            excinfo.value.json['errors']['title'].lower()

    def test_edit_unique_name(self, req, db_session):
        """
        It should allow the cycle to be able to change its unique name
        """
        from datetime import date
        from occams_studies import models

        cycle = models.Cycle(name='week-1', title=u'Week 1', week=1)

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today(),
            cycles=[cycle])

        db_session.add_all([study])
        db_session.flush()

        req.json_body = {
            'name': 'somestudy',
            'title': cycle.title,
            'week': cycle.week
        }

        res = self._call_fut(cycle, req)
        assert res is not None


class TestDeleteJson:

    def _call_fut(self, *args, **kw):
        from occams_studies.views.cycle import delete_json as view
        return view(*args, **kw)

    def test_no_visit(self, req, db_session):
        """
        It should allow deleting of a cycle if it has no visits
        """

        from datetime import date
        from occams_studies import models

        cycle = models.Cycle(name='week-1', title=u'Week 1', week=1)

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today(),
            cycles=[cycle])

        db_session.add_all([study])
        db_session.flush()

        self._call_fut(cycle, req)
        assert 0 == study.cycles.count()

    def test_has_visits(self, req, db_session, config):
        """
        It should not allow deletion of a cycle if it has visit
        (unless administrator)
        """
        from datetime import date
        from pyramid.httpexceptions import HTTPForbidden
        from occams_studies import models

        cycle = models.Cycle(name='week-1', title=u'Week 1', week=1)

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today(),
            cycles=[cycle])

        patient = models.Patient(
            site=models.Site(name='ucsd', title=u'UCSD'),
            pid=u'12345')

        enrollment = models.Enrollment(
            study=study,
            consent_date=date.today(),
            patient=patient)

        visit = models.Visit(
            patient=patient, visit_date=date.today(), cycles=[cycle])

        db_session.add_all([study, enrollment, visit])
        db_session.flush()

        # Should not be able to delete if not an admin
        config.testing_securitypolicy(permissive=False)
        with pytest.raises(HTTPForbidden):
            self._call_fut(cycle, req)

        config.testing_securitypolicy(permissive=True)
        self._call_fut(cycle, req)
        assert 0 == study.cycles.count()
