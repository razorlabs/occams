import pytest


@pytest.yield_fixture
def check_csrf_token(config):
    import mock
    name = 'occams.views.enrollment.check_csrf_token'
    with mock.patch(name) as patch:
        yield patch


class TestViewJson:

    def _call_fut(self, *args, **kw):
        from occams.views.enrollment import view_json as view
        return view(*args, **kw)

    def test_distinguish_ambiguous_enrollment(
            self, req, dbsession, factories):
        """
        It should be able to distiguish which enrollment has randomization data
        """

        schema = factories.SchemaFactory.create()

        study = factories.StudyFactory.create(
            randomization_schema=schema,
            is_randomized=True,
        )

        enrollment1 = factories.EnrollmentFactory(
            study=study,
            stratum=factories.StratumFactory(
                arm__study=study
            )
        )
        entity = factories.EntityFactory.create(schema=schema)
        enrollment1.entities.add(entity)

        enrollment2 = factories.EnrollmentFactory(study=study)

        dbsession.flush()

        res = self._call_fut(enrollment1, req)
        assert res['stratum'] is not None

        res = self._call_fut(enrollment2, req)
        assert res['stratum'] is None

    def test_hide_blinded_randomization(self, req, dbsession, factories):
        """
        It should not include randomization status if study is blinded
        """

        schema = factories.SchemaFactory.create()

        study = factories.StudyFactory.create(
            randomization_schema=schema,
            is_randomized=True,
            is_blinded=True,
        )

        enrollment = factories.EnrollmentFactory(
            study=study,
            stratum=factories.StratumFactory(
                arm__study=study
            )
        )

        entity = factories.EntityFactory.create(schema=schema)
        enrollment.entities.add(entity)

        dbsession.flush()

        res = self._call_fut(enrollment, req)
        assert res['stratum']['arm'] is None

    def test_show_unblinded_randomization(self, req, dbsession, factories):
        """
        It should show randomization status if the study is not blinded
        """

        schema = factories.SchemaFactory.create()

        study = factories.StudyFactory.create(
            randomization_schema=schema,
            is_randomized=True,
            is_blinded=False,
        )

        enrollment = factories.EnrollmentFactory(
            study=study,
            stratum=factories.StratumFactory(
                arm__study=study
            )
        )

        entity = factories.EntityFactory.create(schema=schema)
        enrollment.entities.add(entity)

        dbsession.flush()

        res = self._call_fut(enrollment, req)
        assert res['stratum']['arm'] is not None


class TestEditJson:

    def _call_fut(self, *args, **kw):
        from occams.views.enrollment import edit_json as view
        return view(*args, **kw)

    def test_save(self, req, dbsession, factories):
        from datetime import date
        from occams import models

        study = factories.StudyFactory.create()
        patient = factories.PatientFactory.create()
        dbsession.flush()

        today = date.today()

        payload = {
            'study': str(study.id),
            'consent_date': str(today),
            'latest_consent_date': str(today),
            'termination_date': str(today),
            'reference_number': u'123'
        }

        req.json_body = payload
        res = self._call_fut(patient['enrollments'], req)

        enrollment = dbsession.query(models.Enrollment).get(res['id'])

        actual = {
            'study': str(enrollment.study.id),
            'consent_date': str(enrollment.consent_date),
            'latest_consent_date': str(enrollment.latest_consent_date),
            'termination_date': str(enrollment.termination_date),
            'reference_number': str(enrollment.reference_number)
        }

        assert payload == actual

    def test_unique_consent(self, req, dbsession, factories):
        """
        It should allow multiple enrollments to a study, but a single consent.
        """
        from datetime import date
        from pyramid.httpexceptions import HTTPBadRequest
        from occams import models

        study = factories.StudyFactory.create()
        patient = factories.PatientFactory.create()
        dbsession.flush()

        consent_date = date.today()

        req.json_body = {
            'study': str(study.id),
            'consent_date': str(consent_date),
            'latest_consent_date': str(consent_date),
        }

        self._call_fut(patient['enrollments'], req)

        assert (
            dbsession.query(models.Enrollment)
            .filter_by(patient=patient, study=study)
            .one()) is not None

        # Try adding it again, it should fail
        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(patient['enrollments'], req)

        assert 'This enrollment already exists.' in \
            excinfo.value.json['errors']['consent_date']

    def test_missing_consent(self, req, dbsession, factories):
        """
        It should require latest date
        """

        from datetime import date
        from pyramid.httpexceptions import HTTPBadRequest

        study = factories.StudyFactory.create()
        patient = factories.PatientFactory.create()
        dbsession.flush()

        consent_date = date.today()

        req.json_body = {
            'study': str(study.id),
            'consent_date': None,
            'latest_consent_date': str(consent_date),
        }

        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(patient['enrollments'], req)

        assert 'required' in \
            excinfo.value.json['errors']['consent_date']

    def test_missing_latest_consent(self, req, dbsession, factories):
        """
        It should require latest consent date
        """

        from datetime import date
        from pyramid.httpexceptions import HTTPBadRequest

        study = factories.StudyFactory.create()
        patient = factories.PatientFactory.create()
        dbsession.flush()

        consent_date = date.today()

        req.json_body = {
            'study': str(study.id),
            'consent_date': str(consent_date),
            'latest_consent_date': None
        }

        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(patient['enrollments'], req)

        assert 'required' in \
            excinfo.value.json['errors']['latest_consent_date']

    def test_disable_study_update(self, req, dbsession, factories):
        """
        It should not allow a enrollment's study to be changed
        """
        from datetime import date
        from pyramid.httpexceptions import HTTPBadRequest

        study1 = factories.StudyFactory.create()
        study2 = factories.StudyFactory.create()
        patient = factories.PatientFactory.create()
        enrollment = factories.EnrollmentFactory.create(
            study=study1,
            patient=patient,
            consent_date=study1.consent_date)
        dbsession.flush()

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

    def test_update_patient(self, req, dbsession, factories):
        """
        It should mark the patient as updated
        """
        from datetime import date

        study = factories.StudyFactory.create()
        patient = factories.PatientFactory.create()
        dbsession.flush()

        old_modify_date = patient.modify_date
        req.json_body = {
            'study': study.id,
            'consent_date': str(date.today()),
            'latest_consent_date': str(date.today())
        }

        self._call_fut(patient['enrollments'], req)
        assert old_modify_date < patient.modify_date

    def test_temination_date_disabled_if_form_configured(
            self, req, dbsession, factories):
        """
        Termination date is populated via form when available
        """

        from datetime import date, timedelta

        today = date.today()
        t1 = today - timedelta(days=5)
        t2 = today
        t3 = today + timedelta(days=100)
        t4 = today + timedelta(days=200)

        enrollment = factories.EnrollmentFactory.create(
            study=factories.StudyFactory.create(
                consent_date=t3,
                termination_schema=factories.SchemaFactory.create(
                    publish_date=t1,
                    attributes={
                        'termination_date': factories.AttributeFactory(
                            name='termination_date',
                            type='date'
                        )
                    }
                )
            ),
            patient=factories.PatientFactory.create(),
            consent_date=t1,
            termination_date=t3
        )

        dbsession.flush()

        req.json_body = {
            'study': enrollment.study.id,
            'consent_date': str(t1),
            'latest_consent_date': str(t2),
            'termination_date': str(t4)
        }

        self._call_fut(enrollment, req)

        # Termination date should not have changed because
        # it's controlled via termination schema
        assert t3 == enrollment.termination_date

    def test_temination_date_enabled_if_no_termination(
            self, req, dbsession, factories):
        """
        Termination date is populated directly through form is unavailable
        """

        from datetime import date, timedelta

        today = date.today()
        t1 = today - timedelta(days=5)
        t2 = today
        t3 = today + timedelta(days=100)
        t4 = today + timedelta(days=200)

        enrollment = factories.EnrollmentFactory.create(
            study=factories.StudyFactory.create(
                consent_date=t3,
            ),
            patient=factories.PatientFactory.create(),
            consent_date=t1,
            termination_date=t3
        )
        dbsession.flush()

        req.json_body = {
            'study': enrollment.study.id,
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
        from occams.views.enrollment import delete_json as view
        return view(*args, **kw)

    def test_update_patient(self, req, dbsession, factories):
        """
        It should mark the patient as updated
        """
        enrollment = factories.EnrollmentFactory.create()
        patient = enrollment.patient
        dbsession.flush()

        old_modify_date = patient.modify_date
        self._call_fut(enrollment, req)
        assert old_modify_date < patient.modify_date

    def test_cascade_forms(self, req, dbsession, factories):
        """
        It should also remove termination forms.
        """
        from occams_datastore import models as datastore
        from occams import models

        enrollment = factories.EnrollmentFactory.create()
        enrollment.entities.add(factories.EntityFactory.create())
        dbsession.flush()

        enrollment_id = enrollment.id

        self._call_fut(enrollment, req)

        assert dbsession.query(models.Enrollment).get(enrollment_id) is None
        assert 0 == dbsession.query(datastore.Entity).count()


class Test_terminate_ajax:

    def _call_fut(self, *args, **kw):
        from occams.views.enrollment import terminate_ajax as view
        return view(*args, **kw)

    def test_context_attach_on_create(self, req, dbsession, config, factories):
        """
        It should create a new termination schema and attach when none is found
        """
        import mock
        from webob.multidict import MultiDict

        config.include('pyramid_chameleon')

        termination_schema = factories.SchemaFactory.create()
        termination_schema.attributes['termination_date'] = \
            factories.AttributeFactory.create(
                name='termination_date',
                title='Termination Date',
                type='date',
                order=0
            )
        study = factories.StudyFactory.create(
            termination_schema=termination_schema)
        enrollment = factories.EnrollmentFactory.create(study=study)
        dbsession.flush()

        req.current_route_path = mock.Mock(return_value='/a/b/c')
        req.POST = MultiDict()
        res = self._call_fut(enrollment, req)

        dbsession.refresh(enrollment)

        enrollment_entities = list(enrollment.entities)
        assert len(enrollment_entities)
        assert enrollment_entities[0].schema == termination_schema

        patient_entities = list(enrollment.patient.entities)
        assert len(patient_entities)
        assert patient_entities[0].schema == termination_schema


class Test_randomization_ajax:

    def _call_fut(self, *args, **kw):
        from occams.views.enrollment import randomize_ajax as view
        return view(*args, **kw)

    def test_get_randomized_view(self, req, dbsession, config, factories):
        """
        It should render randomization details for randomized enrollment
        """
        import mock
        from occams.views.enrollment import \
            RAND_INFO_KEY

        config.include('pyramid_chameleon')

        study = factories.StudyFactory.create(
            is_randomized=True,
            randomization_schema=factories.SchemaFactory.create())
        stratum = factories.StratumFactory.create(study=study)
        stratum.entities.add(factories.EntityFactory.create(
            schema=study.randomization_schema))
        enrollment = factories.EnrollmentFactory.create(
            study=study,
            stratum=stratum)
        dbsession.flush()

        req.current_route_path = mock.Mock(return_value='/a/b/c')
        req.session[RAND_INFO_KEY] = None

        res = self._call_fut(enrollment, req)

        assert 'Randomization Status' in res['content']

    def test_get_challenge_view(self, req, dbsession, config, factories):
        """
        It should render the challenge form first when beginning randomization
        """
        import uuid
        import mock
        from webob.multidict import MultiDict
        from occams.views.enrollment import \
            RAND_INFO_KEY, RAND_CHALLENGE

        config.include('pyramid_chameleon')

        study = factories.StudyFactory.create(
            is_randomized=True,
            randomization_schema=factories.SchemaFactory.create())
        enrollment = factories.EnrollmentFactory.create(study=study)
        dbsession.flush()

        procid = str(uuid.uuid4())
        req.current_route_path = mock.Mock(return_value='/a/b/c')
        req.session[RAND_INFO_KEY] = {
            'stage': RAND_CHALLENGE,
            'procid': procid,
            'formdata': None,
        }
        req.GET = MultiDict({'procid': procid})

        res = self._call_fut(enrollment, req)

        assert '(Step 1 of 3)' in res['content']

    def test_get_enter_view(self, req, dbsession, config, factories):
        """
        It should render the enter form when at the ENTER stage
        """
        import uuid
        import mock
        from webob.multidict import MultiDict
        from occams.views.enrollment import \
            RAND_INFO_KEY, RAND_ENTER

        config.include('pyramid_chameleon')

        study = factories.StudyFactory.create(
            is_randomized=True,
            randomization_schema=factories.SchemaFactory.create())
        enrollment = factories.EnrollmentFactory.create(study=study)
        dbsession.flush()

        procid = str(uuid.uuid4())
        req.current_route_path = mock.Mock(return_value='/a/b/c')
        req.session[RAND_INFO_KEY] = {
            'stage': RAND_ENTER,
            'procid': procid,
            'formdata': None,
        }
        req.GET = MultiDict({'procid': procid})

        res = self._call_fut(enrollment, req)

        assert '(Step 2 of 3)' in res['content']

    def test_get_verify_view(self, req, dbsession, config, factories):
        """
        It should render the verify form when at the VERIFY stage
        """
        import uuid
        import mock
        from webob.multidict import MultiDict
        from occams.views.enrollment import \
            RAND_INFO_KEY, RAND_VERIFY

        config.include('pyramid_chameleon')

        study = factories.StudyFactory.create(
            is_randomized=True,
            randomization_schema=factories.SchemaFactory.create())
        enrollment = factories.EnrollmentFactory.create(study=study)
        dbsession.flush()

        procid = str(uuid.uuid4())
        req.current_route_path = mock.Mock(return_value='/a/b/c')
        req.session[RAND_INFO_KEY] = {
            'stage': RAND_VERIFY,
            'procid': procid,
            'formdata': None,
        }
        req.GET = MultiDict({'procid': procid})

        res = self._call_fut(enrollment, req)

        assert '(Step 3 of 3)' in res['content']

    def test_challenge(self, req, dbsession, config, factories):
        """
        It should set to CHALLENGE mode when no session is found
        """
        import mock
        from occams.views.enrollment import \
            RAND_INFO_KEY, RAND_CHALLENGE

        config.include('pyramid_chameleon')

        enrollment = factories.EnrollmentFactory.create(
            study__is_randomized=True,
            study__randomization_schema=factories.SchemaFactory.create(),
        )
        dbsession.flush()

        req.current_route_path = mock.Mock(return_value='/a/b/c')
        req.session[RAND_INFO_KEY] = None

        self._call_fut(enrollment, req)

        assert req.session[RAND_INFO_KEY]['stage'] == RAND_CHALLENGE

    def test_transition_from_enter_to_verify(
            self, req, dbsession, config, factories):
        """
        It should transition from ENTER to VERIFY on successfull submit
        """

        import uuid
        import mock
        from webob.multidict import MultiDict
        from occams.views.enrollment import \
            RAND_INFO_KEY, RAND_ENTER, RAND_VERIFY

        config.include('pyramid_chameleon')

        enrollment = factories.EnrollmentFactory.create(
            study__is_randomized=True,
            study__randomization_schema=factories.SchemaFactory.create(),
        )

        procid = str(uuid.uuid4())
        req.current_route_path = mock.Mock(return_value='/a/b/c')
        req.session[RAND_INFO_KEY] = {
            'procid': procid,
            'stage': RAND_ENTER,
            'formdata': {}
        }
        req.method = 'POST'
        req.POST = MultiDict({'procid': procid})

        self._call_fut(enrollment, req)

        assert req.session[RAND_INFO_KEY]['stage'] == RAND_VERIFY

    def test_transition_from_verify_to_complete(
            self, req, dbsession, config, factories):
        """
        It should randomize the patient on successful submit from VERIFY
        """

        import uuid
        import mock
        from webob.multidict import MultiDict
        from occams.views.enrollment import \
            RAND_INFO_KEY, RAND_VERIFY

        config.include('pyramid_chameleon')
        req.method = 'POST'
        req.POST = MultiDict()

        enrollment = factories.EnrollmentFactory.create(
            study__is_randomized=True,
            study__randomization_schema=factories.SchemaFactory.create(),
        )
        stratum = factories.StratumFactory(study=enrollment.study)
        stratum.entities.add(factories.EntityFactory.create(
            schema=enrollment.study.randomization_schema
        ))
        dbsession.flush()

        procid = str(uuid.uuid4())
        req.current_route_path = mock.Mock(return_value='/a/b/c')
        req.session[RAND_INFO_KEY] = {
            'procid': procid,
            'stage': RAND_VERIFY,
            'formdata': {}
        }
        req.POST = MultiDict({'procid': procid})

        self._call_fut(enrollment, req)

        assert RAND_INFO_KEY not in req.session

    def test_randid_assignment(self, req, dbsession, config, factories):
        """
        It should assign randomiation ids sequentially
        """

        import uuid
        import mock
        from webob.multidict import MultiDict
        from occams.views.enrollment import \
            RAND_INFO_KEY, RAND_VERIFY

        config.include('pyramid_chameleon')

        req.method = 'POST'
        req.POST = MultiDict()

        study = factories.StudyFactory.create(
            is_randomized=True,
            randomization_schema=factories.SchemaFactory.create())
        stratum1 = factories.StratumFactory(study=study)
        stratum1.entities.add(factories.EntityFactory.create(
            schema=study.randomization_schema
        ))
        stratum2 = factories.StratumFactory(study=study)
        stratum2.entities.add(factories.EntityFactory.create(
            schema=study.randomization_schema
        ))

        enrollment1 = factories.EnrollmentFactory.create(study=study)
        enrollment2 = factories.EnrollmentFactory.create(study=study)
        dbsession.flush()

        procid = str(uuid.uuid4())
        req.current_route_path = mock.Mock(return_value='/a/b/c')
        req.session[RAND_INFO_KEY] = {
            'procid': procid,
            'stage': RAND_VERIFY,
            'formdata': {}
        }
        req.POST = MultiDict({'procid': procid})

        res = self._call_fut(enrollment1, req)

        dbsession.refresh(enrollment1)

        assert res.status_code == 302
        assert enrollment1.stratum == stratum1

        req.session[RAND_INFO_KEY] = {
            'procid': procid,
            'stage': RAND_VERIFY,
            'formdata': {}
        }
        req.POST = MultiDict({'procid': procid})
        res = self._call_fut(enrollment2, req)

        dbsession.refresh(enrollment2)

        assert res.status_code == 302
        assert enrollment2.stratum == stratum2

    def test_randid_assignment_with_criteria(
            self, req, dbsession, config, factories):
        """
        It should assign a randid given the criteria associated with a stratum
        """
        import uuid
        import mock
        from webob.multidict import MultiDict
        from occams.views.enrollment import \
            RAND_INFO_KEY, RAND_VERIFY

        schema = factories.SchemaFactory.create(
            attributes={
                u'likes_icecream': factories.AttributeFactory.create(
                    name=u'likes_icecream',
                    type=u'choice',
                    choices={
                        u'0': factories.ChoiceFactory.create(name=u'0'),
                        u'1': factories.ChoiceFactory.create(name=u'1'),
                    },
                )
            }
        )

        study = factories.StudyFactory.create(
            randomization_schema=schema,
            is_randomized=True
        )

        stratum1 = factories.StratumFactory.create(study=study)
        stratum2 = factories.StratumFactory.create(study=study)

        entity1 = factories.EntityFactory.create(schema=schema)
        entity1['likes_icecream'] = u'0'
        stratum1.entities.add(entity1)

        # If we submit yes, we'll be put into the 'fake sugar' arm of the study
        entity2 = factories.EntityFactory.create(schema=schema)
        entity2['likes_icecream'] = u'1'
        stratum2.entities.add(entity2)

        enrollment = factories.EnrollmentFactory.create(study=study)
        dbsession.flush()

        config.include('pyramid_chameleon')

        procid = str(uuid.uuid4())
        req.current_route_path = mock.Mock(return_value='/a/b/c')
        req.method = 'POST'
        payload = {'procid': procid, 'likes_icecream': u'1'}
        req.POST = MultiDict(payload)
        req.session[RAND_INFO_KEY] = {
            'procid': procid,
            'stage': RAND_VERIFY,
            'formdata': payload
        }
        res = self._call_fut(enrollment, req)

        dbsession.refresh(enrollment)

        assert res.status_code == 302
        assert enrollment.stratum == stratum2

    def test_multiple_randomization(self, req, dbsession, config, factories):
        """
        It should return a flash message to the user indicating more than
        one randomization is in progress
        """
        import uuid
        import mock
        from webob.multidict import MultiDict
        from occams.views.enrollment import \
            RAND_INFO_KEY, RAND_ENTER, RAND_VERIFY

        config.include('pyramid_chameleon')

        enrollment = factories.EnrollmentFactory.create(
            study__is_randomized=True,
            study__randomization_schema=factories.SchemaFactory.create(),
        )

        procid = str(uuid.uuid4())
        req.current_route_path = mock.Mock(return_value='/a/b/c')
        req.session[RAND_INFO_KEY] = {
            'procid': procid,
            'stage': RAND_ENTER,
            'formdata': {}
        }
        req.method = 'POST'
        req.POST = MultiDict({'procid': procid})

        self._call_fut(enrollment, req)

        assert req.session[RAND_INFO_KEY]['stage'] == RAND_VERIFY

        # new randomization with different uuid
        procid = str(uuid.uuid4())
        req.current_route_path = mock.Mock(return_value='/a/b/c')

        req.method = 'POST'
        req.POST = MultiDict({'procid': procid})

        res = self._call_fut(enrollment, req)

        msg = u'You have another randomization in progress, starting over.'

        assert req.session.pop_flash('warning')[0] == msg

    def test_randomizing_a_randomized_patient(
            self, req, dbsession, config, factories):
        """
        It should return a msg indicating the patient is already randomized.
        """
        import uuid
        import mock
        from webob.multidict import MultiDict
        from occams.views.enrollment import \
            RAND_INFO_KEY, RAND_CHALLENGE

        config.include('pyramid_chameleon')
        req.method = 'POST'
        req.POST = MultiDict()

        study = factories.StudyFactory.create(
            is_randomized=True,
            randomization_schema=factories.SchemaFactory.create())
        stratum = factories.StratumFactory.create(study=study)
        stratum.entities.add(factories.EntityFactory.create(
            schema=study.randomization_schema))
        enrollment = factories.EnrollmentFactory.create(
            study=study,
            stratum=stratum
        )
        dbsession.flush()

        procid = str(uuid.uuid4())
        req.current_route_path = mock.Mock(return_value='/a/b/c')
        req.session[RAND_INFO_KEY] = {
            'procid': procid,
            'stage': RAND_CHALLENGE,
            'formdata': {}
        }
        req.POST = MultiDict({'procid': procid})

        self._call_fut(enrollment, req)

        msg = u'This patient is already randomized for this study'

        assert req.session.pop_flash('warning')[0] == msg

    def test_transition_from_challenge_to_enter(
            self, req, dbsession, config, factories):
        """
        It should transition from CHALLENGE to ENTER on successfull submit.
        """
        import uuid
        import mock
        from webob.multidict import MultiDict
        from occams.views.enrollment import \
            RAND_CHALLENGE, RAND_INFO_KEY, RAND_ENTER

        config.include('pyramid_chameleon')

        enrollment = factories.EnrollmentFactory.create(
            study__is_randomized=True,
            study__randomization_schema=factories.SchemaFactory.create(),
        )
        dbsession.flush()

        procid = str(uuid.uuid4())
        req.current_route_path = mock.Mock(return_value='/a/b/c')
        payload = {
            'procid': procid,
            'confirm': enrollment.reference_number
        }
        req.session[RAND_INFO_KEY] = {
            'procid': procid,
            'stage': RAND_CHALLENGE,
            'formdata': payload
        }
        req.method = 'POST'

        req.POST = MultiDict(payload)

        self._call_fut(enrollment, req)

        assert req.session[RAND_INFO_KEY]['stage'] == RAND_ENTER

    def test_challenge_form_doesnt_validate(
            self, req, dbsession, config, factories):
        """It should raise an exception if the form validation fails."""
        import uuid
        import mock
        from webob.multidict import MultiDict
        from pyramid.httpexceptions import HTTPBadRequest
        from occams.views.enrollment import \
            RAND_CHALLENGE, RAND_INFO_KEY

        config.include('pyramid_chameleon')

        enrollment = factories.EnrollmentFactory.create(
            study__is_randomized=True,
            study__randomization_schema=factories.SchemaFactory.create(),
        )
        dbsession.flush()

        procid = str(uuid.uuid4())
        req.current_route_path = mock.Mock(return_value='/a/b/c')
        payload = {
            'procid': procid,
            'confirm': 'incorrect_study_number'
        }
        req.session[RAND_INFO_KEY] = {
            'procid': procid,
            'stage': RAND_CHALLENGE,
            'formdata': payload
        }
        req.method = 'POST'

        req.POST = MultiDict(payload)

        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(enrollment, req)

    def test_enter_form_doesnt_validate(
            self, req, dbsession, config, factories):
        """It should raise an exception if the form validation fails."""

        import uuid
        import mock
        from webob.multidict import MultiDict
        from pyramid.httpexceptions import HTTPBadRequest
        from occams.views.enrollment import \
            RAND_INFO_KEY, RAND_ENTER
        config.include('pyramid_chameleon')

        enrollment = factories.EnrollmentFactory.create(
            study__is_randomized=True,
            study__randomization_schema=factories.SchemaFactory.create(),
        )

        procid = str(uuid.uuid4())
        req.current_route_path = mock.Mock(return_value='/a/b/c')

        req.session[RAND_INFO_KEY] = {
            'procid': procid,
            'stage': RAND_ENTER,
            'formdata': {}
        }
        req.method = 'POST'
        req.POST = MultiDict({'procid': procid})

        with mock.patch('occams.views.enrollment.make_form') as mock_form:
            validate_obj = mock.Mock()
            validate_obj.return_value = [0, 1]
            validate_obj.validate.return_value = False
            mock_form_obj = mock.Mock()
            mock_form_obj.return_value = validate_obj
            mock_form.return_value = mock_form_obj

            with mock.patch('occams.views.enrollment.wtferrors') as mock_wtf:
                mock_wtf.return_value = u''

                with pytest.raises(HTTPBadRequest) as excinfo:
                    self._call_fut(enrollment, req)

    def test_verify_form_doesnt_validate(
            self, req, dbsession, config, factories):
        """It should raise an exception if the form validation fails."""

        import uuid
        import mock
        from webob.multidict import MultiDict
        from pyramid.httpexceptions import HTTPBadRequest
        from occams.views.enrollment import \
            RAND_INFO_KEY, RAND_VERIFY
        config.include('pyramid_chameleon')

        enrollment = factories.EnrollmentFactory.create(
            study__is_randomized=True,
            study__randomization_schema=factories.SchemaFactory.create(),
        )

        procid = str(uuid.uuid4())
        req.current_route_path = mock.Mock(return_value='/a/b/c')

        req.session[RAND_INFO_KEY] = {
            'procid': procid,
            'stage': RAND_VERIFY,
            'formdata': {}
        }
        req.method = 'POST'
        req.POST = MultiDict({'procid': procid})

        with mock.patch('occams.views.enrollment.make_form') as mock_form:
            validate_obj = mock.Mock()
            validate_obj.return_value = [0, 1]
            validate_obj.validate.return_value = False
            mock_form_obj = mock.Mock()
            mock_form_obj.return_value = validate_obj
            mock_form.return_value = mock_form_obj

            with mock.patch('occams.views.enrollment.wtferrors') as mock_wtf:
                mock_wtf.return_value = u''

                with pytest.raises(HTTPBadRequest) as excinfo:
                    self._call_fut(enrollment, req)

    def test_verify_fails(
            self, req, dbsession, config, factories):
        """It should return a msg that verify data doesn't match entered data."""

        import uuid
        import mock
        from webob.multidict import MultiDict
        from occams.views.enrollment import \
            RAND_INFO_KEY, RAND_VERIFY, RAND_ENTER

        config.include('pyramid_chameleon')

        schema = factories.SchemaFactory.create(
            attributes={
                u'field': factories.AttributeFactory.create(
                    name=u'field',
                    type=u'string'
                )
            }
        )

        enrollment = factories.EnrollmentFactory.create(
            study__is_randomized=True,
            study__randomization_schema=schema
        )

        procid = str(uuid.uuid4())
        req.current_route_path = mock.Mock(return_value='/a/b/c')

        req.session[RAND_INFO_KEY] = {
            'procid': procid,
            'stage': RAND_VERIFY,
            'formdata': {'field': 'correct_value'}
        }

        payload = {
            'procid': procid,
            'field': u'incorrect_value'
        }
        req.method = 'POST'
        req.POST = MultiDict(payload)
        self._call_fut(enrollment, req)

        partial_msg = u'do not match'

        assert req.session[RAND_INFO_KEY]['stage'] == RAND_ENTER
        assert partial_msg in req.session.pop_flash('warning')[0]

    def test_no_randid_numbers_left(self, req, dbsession, config, factories):
        """
        It should create an HTTPBadResponse when rand numbers are depleted
        """

        import uuid
        import mock
        from webob.multidict import MultiDict
        from pyramid.httpexceptions import HTTPBadRequest
        from occams.views.enrollment import \
            RAND_INFO_KEY, RAND_VERIFY

        config.include('pyramid_chameleon')

        req.method = 'POST'
        req.POST = MultiDict()

        study = factories.StudyFactory.create(
            is_randomized=True,
            randomization_schema=factories.SchemaFactory.create())

        enrollment1 = factories.EnrollmentFactory.create(study=study)
        dbsession.flush()

        procid = str(uuid.uuid4())
        req.current_route_path = mock.Mock(return_value='/a/b/c')
        req.session[RAND_INFO_KEY] = {
            'procid': procid,
            'stage': RAND_VERIFY,
            'formdata': {}
        }
        req.POST = MultiDict({'procid': procid})

        dbsession.refresh(enrollment1)

        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(enrollment1, req)

        assert 'numbers depleted' in excinfo.value.body

    def test_restart_on_invalid_stage(
            self, req, dbsession, config, factories):
        """
        It should restart the process when unknown stage is detected.
        This should never happen, but if it does it is logged.
        """
        import uuid
        import mock
        from webob.multidict import MultiDict
        from occams.views.enrollment import RAND_INFO_KEY

        config.include('pyramid_chameleon')

        study = factories.StudyFactory.create(
            is_randomized=True,
            randomization_schema=factories.SchemaFactory.create())
        enrollment = factories.EnrollmentFactory.create(study=study)
        dbsession.flush()

        procid = str(uuid.uuid4())
        req.method = 'POST'
        req.current_route_path = mock.Mock(return_value='/a/b/c')
        req.session[RAND_INFO_KEY] = {
            'procid': procid,
            'stage': 'bogus',
            'formdata': {}
        }
        req.POST = MultiDict({'procid': procid})

        res = self._call_fut(enrollment, req)

        assert res.status_code == 302
        assert 'Unable to determine' in req.session.peek_flash('warning')[0]
        assert RAND_INFO_KEY not in req.session
