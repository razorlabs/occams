import pytest


class TestViewJson:

    def _call_fut(self, *args, **kw):
        from occams_studies.views.enrollment import view_json as view
        return view(*args, **kw)

    def test_hide_blinded_randomization(self, req, db_session):
        """
        It should not include randomization status if study is blinded
        """
        from datetime import date
        from occams_studies import models

        schema = models.Schema(name=u'criteria', title=u'Criteria')

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today(),
            randomization_schema=schema,
            is_randomized=True)

        enrollment = models.Enrollment(
            patient=models.Patient(
                site=models.Site(name=u'ucsd', title=u'UCSD'),
                pid=u'12345'),
            study=study,
            consent_date=date.today(),
            stratum=models.Stratum(
                randid=u'98765',
                block_number='111',
                study=study,
                arm=models.Arm(
                    name=u'tested',
                    title=u'Tested',
                    study=study)))

        db_session.add(enrollment)
        db_session.flush()

        study.is_blinded = False
        db_session.flush()
        res = self._call_fut(enrollment, req)
        assert res['stratum']['arm'] is not None

        study.is_blinded = True
        db_session.flush()
        res = self._call_fut(enrollment, req)
        assert res['stratum']['arm'] is None


class TestEditJson:

    def _call_fut(self, *args, **kw):
        from occams_studies.views.enrollment import edit_json as view
        return view(*args, **kw)

    def test_save(self, req, db_session):
        from datetime import date
        from occams_studies import models

        today = date.today()

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=today,
            consent_date=today)

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        db_session.add_all([patient, study])
        db_session.flush()

        payload = {
            'study': str(study.id),
            'consent_date': str(today),
            'latest_consent_date': str(today),
            'termination_date': str(today),
            'reference_number': u'123'
        }

        req.json_body = payload
        res = self._call_fut(patient['enrollments'], req)

        enrollment = db_session.query(models.Enrollment).get(res['id'])

        actual = {
            'study': str(enrollment.study.id),
            'consent_date': str(enrollment.consent_date),
            'latest_consent_date': str(enrollment.latest_consent_date),
            'termination_date': str(enrollment.termination_date),
            'reference_number': str(enrollment.reference_number)
        }

        assert payload == actual

    def test_unique_consent(self, req, db_session):
        """
        It should allow multiple enrollments to a study, but a single consent.
        """
        from datetime import date
        from pyramid.httpexceptions import HTTPBadRequest
        import pytest
        from occams_studies import models

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today())

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        db_session.add_all([patient, study])
        db_session.flush()

        consent_date = date.today()

        req.json_body = {
            'study': str(study.id),
            'consent_date': str(consent_date),
            'latest_consent_date': str(consent_date),
        }

        self._call_fut(patient['enrollments'], req)

        assert (
            db_session.query(models.Enrollment)
            .filter_by(patient=patient, study=study)
            .one()) is not None

        # Try adding it again, it should fail
        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(patient['enrollments'], req)

        assert 'This enrollment already exists.' in \
            excinfo.value.json['errors']['consent_date']

    def test_disable_study_update(self, req, db_session):
        """
        It should not allow a enrollment's study to be changed
        """
        from datetime import date
        from pyramid.httpexceptions import HTTPBadRequest
        import pytest
        from occams_studies import models

        study1 = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today())

        study2 = models.Study(
            name=u'otherstudy',
            title=u'Other Study',
            short_title=u'ostudy',
            code=u'111',
            start_date=date.today(),
            consent_date=date.today())

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        enrollment = models.Enrollment(
            study=study1,
            patient=patient,
            consent_date=date.today())

        db_session.add_all([patient, enrollment, study1, study2])
        db_session.flush()

        consent_date = date.today()

        req.json_body = {
            'study': str(study2.id),
            'consent_date': str(consent_date),
            'latest_consent_date': str(consent_date),
        }

        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(enrollment, req)

        assert 'Cannot change an enrollment\'s study.' in \
            excinfo.value.json['errors']['study']

    def test_timeline_start_date(self, req, db_session):
        """
        It should not allow consent dates before the study start date
        """
        from datetime import date, timedelta
        from pyramid.httpexceptions import HTTPBadRequest
        import pytest
        from occams_studies import models

        today = date.today()
        invalid_date = today - timedelta(days=100)
        t1 = today - timedelta(days=5)
        t2 = today

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=t1,
            consent_date=t2)

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        db_session.add_all([patient, study])
        db_session.flush()

        req.json_body = {
            'study': str(study.id),
            'consent_date': str(invalid_date),
            'latest_consent_date': str(invalid_date),
        }

        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(patient['enrollments'], req)

        assert 'Cannot enroll before the study start date' in \
            excinfo.value.json['errors']['latest_consent_date']

    def test_timeline_end_date(self, req, db_session):
        """
        It should not allow consent dates after the study end date
        """
        from datetime import date, timedelta
        from pyramid.httpexceptions import HTTPBadRequest
        import pytest
        from occams_studies import models

        today = date.today()
        t1 = today - timedelta(days=5)
        t2 = today
        t3 = today + timedelta(days=100)
        invalid_date = today + timedelta(days=200)

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=t1,
            end_date=t3,
            consent_date=t2)

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        db_session.add_all([patient, study])
        db_session.flush()

        req.json_body = {
            'study': str(study.id),
            'consent_date': str(invalid_date),
            'latest_consent_date': str(invalid_date),
        }

        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(patient['enrollments'], req)

        assert 'Cannot enroll after the study end date' in \
            excinfo.value.json['errors']['latest_consent_date']

    def test_update_patient(self, req, db_session):
        """
        It should mark the patient as updated
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

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        db_session.add_all([patient, study])
        db_session.flush()

        old_modify_date = patient.modify_date
        req.json_body = {
            'study': study.id,
            'consent_date': str(date.today()),
            'latest_consent_date': str(date.today())
        }

        self._call_fut(patient['enrollments'], req)
        assert old_modify_date < patient.modify_date

    def test_temination_date_disabled_if_form_configured(
            self, req, db_session):

        from datetime import date, timedelta
        from occams_studies import models

        today = date.today()
        t1 = today - timedelta(days=5)
        t2 = today
        t3 = today + timedelta(days=100)
        t4 = today + timedelta(days=200)

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=t1,
            consent_date=t3,
            termination_schema=models.Schema(
                name=u'termination',
                title=u'Termination',
                publish_date=t1,
                attributes={
                    'termination_date': models.Attribute(
                        name=u'termination_date',
                        title=u'Termination Date',
                        type=u'date',
                        order=0)
                }))

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        enrollment = models.Enrollment(
            study=study,
            patient=patient,
            consent_date=t1,
            termination_date=t3)

        db_session.add_all([enrollment])
        db_session.flush()

        req.json_body = {
            'study': study.id,
            'consent_date': str(t1),
            'latest_consent_date': str(t2),
            'termination_date': str(t4)
        }

        self._call_fut(enrollment, req)

        # Termination date should not have changed because
        # it's controlled via termination schema
        assert t3 == enrollment.termination_date

    def test_temination_date_enabled_if_no_termination(
            self, req, db_session):

        from datetime import date, timedelta
        from occams_studies import models

        today = date.today()
        t1 = today - timedelta(days=5)
        t2 = today
        t3 = today + timedelta(days=100)
        t4 = today + timedelta(days=200)

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=t1,
            consent_date=t3)

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        enrollment = models.Enrollment(
            study=study,
            patient=patient,
            consent_date=t1,
            termination_date=t3)

        db_session.add_all([enrollment])
        db_session.flush()

        req.json_body = {
            'study': study.id,
            'consent_date': str(t1),
            'latest_consent_date': str(t2),
            'termination_date': str(t4)
        }

        self._call_fut(enrollment, req)

        # Termination date should have changed because there
        # is not termination schema that controls it
        assert t4 == enrollment.termination_date


class TestDeleteJson:

    def _call_fut(self, *args, **kw):
        from occams_studies.views.enrollment import delete_json as view
        return view(*args, **kw)

    def test_update_patient(self, req, db_session):
        """
        It should mark the patient as updated
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

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        enrollment = models.Enrollment(
            study=study,
            patient=patient,
            consent_date=date.today())

        db_session.add_all([patient, enrollment, study])
        db_session.flush()

        old_modify_date = patient.modify_date
        self._call_fut(enrollment, req)
        assert old_modify_date < patient.modify_date

    def test_cascade_forms(self, req, db_session):
        """
        It should also remove termination forms.
        """
        from datetime import date
        from occams_studies import models

        schema = models.Schema(
            name=u'termination',
            title=u'Termination',
            publish_date=date.today())

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today())

        patient = models.Patient(
            site=models.Site(name=u'ucsd', title=u'UCSD'),
            pid=u'12345')

        enrollment = models.Enrollment(
            study=study,
            patient=patient,
            consent_date=date.today())

        enrollment.entities.add(models.Entity(
            schema=schema,
            collect_date=date.today()))

        db_session.add_all([patient, enrollment, study])
        db_session.flush()

        enrollment_id = enrollment.id

        self._call_fut(enrollment, req)

        assert db_session.query(models.Enrollment).get(enrollment_id) is None
        assert 0 == db_session.query(models.Entity).count()


class TestRandomizeAjax:

    @pytest.fixture(autouse=True)
    def install_randomization_data(self, db_session):

        from datetime import date
        from occams_studies import models

        self.schema = models.Schema(
            name=u'criteria', title=u'Criteria', publish_date=date.today())

        self.study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'study',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today(),
            randomization_schema=self.schema,
            is_randomized=True)

        self.stratum = models.Stratum(
            randid=u'98765',
            block_number='111',
            study=self.study,
            arm=models.Arm(
                name=u'tested',
                title=u'Tested',
                study=self.study))

        self.stratum2 = models.Stratum(
            randid=u'98766',
            block_number='111',
            study=self.study,
            arm=models.Arm(
                name=u'tested2',
                title=u'Tested2',
                study=self.study))

        self.stratum.entities.add(models.Entity(schema=self.schema))
        self.stratum2.entities.add(models.Entity(schema=self.schema))

        self.site = models.Site(name=u'ucsd', title=u'UCSD')

        self.enrollment = models.Enrollment(
            patient=models.Patient(
                site=self.site,
                pid=u'12345'),
            study=self.study,
            consent_date=date.today())

        self.enrollment2 = models.Enrollment(
            patient=models.Patient(
                site=self.site,
                pid=u'12346'),
            study=self.study,
            consent_date=date.today())

        db_session.add_all(
            [self.study, self.stratum, self.stratum2,
             self.enrollment, self.enrollment2])
        db_session.flush()

    def _call_fut(self, *args, **kw):
        from occams_studies.views.enrollment import randomize_ajax as view
        return view(*args, **kw)

    def test_challenge(self, req, db_session, config):

        config.include('pyramid_chameleon')
        req.session = {}

        enrollment = self.enrollment

        self._call_fut(enrollment, req)

        assert req.session['randomization_stage'] == 0

    def test_transition_from_enter_to_verify(self, req, db_session, config):

        from webob.multidict import MultiDict

        config.include('pyramid_chameleon')
        payload = MultiDict()
        req.method = 'POST'
        req.POST = payload
        req.matchdict = {
            'patient': self.enrollment.patient,
            'enrollment': self.enrollment
        }

        enrollment = self.enrollment

        req.session['randomization_stage'] = 1

        self._call_fut(enrollment, req)

        assert req.session['randomization_stage'] == 2

    def test_transition_from_verify_to_complete(self, req, db_session, config):

        from webob.multidict import MultiDict

        config.include('pyramid_chameleon')
        payload = MultiDict()
        req.method = 'POST'
        req.POST = payload
        req.matchdict = {
            'patient': self.enrollment.patient,
            'enrollment': self.enrollment
        }

        enrollment = self.enrollment

        req.session['randomization_stage'] = 2

        self._call_fut(enrollment, req)

        assert req.session['randomization_stage'] == 3

    def test_randid_assignment(self, req, db_session, config):

        from webob.multidict import MultiDict

        config.include('pyramid_chameleon')
        payload = MultiDict()

        req.method = 'POST'
        req.POST = payload
        req.matchdict = {
            'patient': self.enrollment.patient,
            'enrollment': self.enrollment
        }

        enrollment = self.enrollment

        req.session['randomization_stage'] = 2

        res = self._call_fut(enrollment, req)

        assert res['enrollment']['stratum']['randid'] == u'98765'
        assert res['enrollment']['stratum']['arm']['name'] == u'tested'

        req.POST = payload
        req.matchdict = {
            'patient': self.enrollment2.patient,
            'enrollment': self.enrollment2
        }

        enrollment = self.enrollment2

        req.session['randomization_stage'] = 2
        res = self._call_fut(enrollment, req)

        assert res['enrollment']['stratum']['randid'] == u'98766'
        assert res['enrollment']['stratum']['arm']['name'] == u'tested2'


class TestRandomizeAjaxAssigned:
    """
    Move this test to it's own class because we need to tweak the criteria
    slightly to make it work for criteria-based randid assigment.
    """

    def _call_fut(self, *args, **kw):
        from occams_studies.views.enrollment import randomize_ajax as view
        return view(*args, **kw)

    def test_randid_assignment_with_criteria(self, req, db_session, config):
        """
        It should assign a randid given the criteria associated with a stratum
        """
        from datetime import date
        from webob.multidict import MultiDict
        from occams_studies import models

        schema = models.Schema(
            name=u'criteria', title=u'Criteria', publish_date=date.today(),
            attributes={
                u'likes_icecream': models.Attribute(
                    name=u'likes_icecream',
                    title=u'Likes Ice Createm',
                    type=u'choice',
                    choices={
                        u'0': models.Choice(name=u'0', title=u'No', order=0),
                        u'1': models.Choice(name=u'1', title=u'Yes', order=1),
                    },
                    order=0,
                )
            })

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'study',
            code=u'000',
            start_date=date.today(),
            consent_date=date.today(),
            randomization_schema=schema,
            is_randomized=True)

        stratum = models.Stratum(
            randid=u'98765',
            block_number='111',
            study=study,
            arm=models.Arm(
                name=u'real-sugar',
                title=u'Real Sugar',
                study=study))

        stratum2 = models.Stratum(
            randid=u'98766',
            block_number='111',
            study=study,
            arm=models.Arm(
                name=u'fake-sugar',
                title=u'Fake Sugar',
                study=study))

        entity1 = models.Entity(schema=schema)
        entity1['likes_icecream'] = u'0'
        stratum.entities.add(entity1)

        # If we submit yes, we'll be put into the 'fake sugar' arm of the study
        entity2 = models.Entity(schema=schema)
        entity2['likes_icecream'] = u'1'
        stratum2.entities.add(entity2)

        enrollment = models.Enrollment(
            patient=models.Patient(
                site=models.Site(name=u'ucsd', title=u'UCSD'),
                pid=u'12345'),
            study=study,
            consent_date=date.today())

        db_session.add_all([study, stratum, stratum2, enrollment])
        db_session.flush()

        config.include('pyramid_chameleon')
        payload = MultiDict([('likes_icecream', u'1')])

        req.method = 'POST'
        req.POST = payload
        req.matchdict = {
            'patient': enrollment.patient,
            'enrollment': enrollment
        }
        req.session['randomization_stage'] = 2

        res = self._call_fut(enrollment, req)

        assert res['enrollment']['stratum']['randid'] == u'98766'
