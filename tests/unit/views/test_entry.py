import pytest


class Test_view_json:

    def _call_fut(self, *args, **kw):
        from occams.views.entry import view_json as view
        return view(*args, **kw)

    def test_with_state(self, req, dbsession):
        """
        It should generate state data is available
        """
        from datetime import date
        import mock
        from occams import models

        myfirst = models.Schema(
            name=u'myfirst',
            title=u'My First Schema',
            publish_date=date.today()
        )
        mydata = models.Entity(
            schema=myfirst,
            state=(
                dbsession.query(models.State)
                .filter_by(name=u'pending-entry')
                .one()))
        dbsession.add(mydata)
        dbsession.flush()
        mydata.__parent__ = mock.MagicMock()
        mydata.__parent__.__parent__ = mock.MagicMock()

        req.session.changed = mock.Mock()
        res = self._call_fut(mydata, req)

        assert res['state'] is not None

    def test_without_state(self, req, dbsession):
        """
        It should generate none if no state data is available
        """
        import mock
        from occams import models
        from datetime import date

        myfirst = models.Schema(
            name=u'myfirst',
            title=u'My First Schema',
            publish_date=date.today()
        )
        mydata = models.Entity(schema=myfirst)
        dbsession.add(mydata)
        dbsession.flush()
        mydata.__parent__ = mock.MagicMock()
        mydata.__parent__.__parent__ = mock.MagicMock()

        req.session.changed = mock.Mock()
        res = self._call_fut(mydata, req)

        assert res['state'] is None


class Test_available_schemata:

    def _call_fut(self, *args, **kw):
        from occams.views.entry import available_schemata as view
        return view(*args, **kw)

    def test_exclude_retracted(self, req, dbsession, config, factories):
        """
        It should not include metadata when rendering via AJAX
        """
        from datetime import date
        from webob.multidict import MultiDict

        schema = factories.SchemaFactory.create(
            publish_date=date.today(), retract_date=date.today())
        study = factories.StudyFactory.create(schemata=set([schema]))
        visit = factories.VisitFactory()
        dbsession.flush()

        req.context = context = visit
        req.GET = MultiDict([('term', schema.title)])
        res = self._call_fut(context, req)

        assert len(res['schemata']) == 0, 'Retracted form was not excluded'


class Test_markup_ajax:

    def _call_fut(self, *args, **kw):
        from occams.views.entry import markup_ajax as view
        return view(*args, **kw)

    def test_no_metadata(self, req, dbsession, config, factories):
        """
        It should not include metadata when rendering via AJAX
        """
        from bs4 import BeautifulSoup
        from webob.multidict import MultiDict

        config.include('pyramid_chameleon')

        entity = factories.EntityFactory()
        dbsession.flush()

        req.context = context = entity
        req.POST = MultiDict()
        req.GET = MultiDict([
            ('version', str(entity.schema.publish_date))
        ])
        res = self._call_fut(context, req)

        soup = BeautifulSoup(res)
        assert len(soup.find_all(class_='entity')) < 1, \
            'Found entity metada when it should not have'


class Test_add_json:

    def _call_fut(self, *args, **kw):
        from occams.views.entry import add_json as view
        return view(*args, **kw)

    def test_add_to_patient(self, req, dbsession):
        from datetime import date
        from occams import models

        schema = models.Schema(
            name=u'schema',
            title=u'Schema',
            publish_date=date.today())

        study = models.Study(
            name='some-study',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            consent_date=date.today(),
            schemata=set([schema]))

        site = models.Site(name=u'somewhere', title=u'Somewhere')
        patient = models.Patient(pid=u'12345', site=site)

        dbsession.add_all([study, patient])
        dbsession.flush()

        req.method = 'POST'
        req.matchdict = {'patient': patient}
        req.json_body = {
            'schema': schema.id,
            'collect_date': str(date.today()),
        }
        factory = models.FormFactory(req)
        factory.__parent__ = patient
        self._call_fut(factory, req)

        contexts = dbsession.query(models.Context).all()

        assert len(contexts) == 1
        assert contexts[0].entity.schema == schema

    def test_add_to_visit(self, req, dbsession):
        from datetime import date
        from occams import models

        schema = models.Schema(
            name=u'schema',
            title=u'Schema',
            publish_date=date.today())

        study = models.Study(
            name='some-study',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            consent_date=date.today(),
            schemata=set([schema]))

        cycle = models.Cycle(
            study=study,
            name=u'cycle-1',
            title=u'Cycle')

        site = models.Site(name=u'somewhere', title=u'Somewhere')
        patient = models.Patient(pid=u'12345', site=site)

        visit = models.Visit(
            patient=patient, visit_date=date.today(), cycles=[cycle])

        dbsession.add_all([study, patient, visit])
        dbsession.flush()

        req.matchdict = {'patient': patient, 'visit': visit}
        req.json_body = {
            'schema': schema.id,
            'collect_date': str(date.today()),
        }
        factory = models.FormFactory(req)
        factory.__parent__ = visit
        self._call_fut(factory, req)

        contexts = dbsession.query(models.Context).all()

        assert len(contexts) == 2
        assert sorted(['patient', 'visit']) == \
            sorted([c.external for c in contexts])

    def test_multiple(self, req, dbsession):
        """
        It should allow adding multiple instances of the same form
        TODO: cant do multiple, no time
        """

    def test_not_in_study(self, req, dbsession):
        """
        It should fail if the form is not part of the study
        """
        from datetime import date, timedelta
        from pyramid.httpexceptions import HTTPBadRequest
        from occams import models

        cycle = models.Cycle(name='week-1', title=u'', week=1)

        schema = models.Schema(
            name=u'sample', title=u'', publish_date=date.today())

        study = models.Study(
            name=u'somestudy',
            title=u'Some Study',
            short_title=u'sstudy',
            code=u'000',
            consent_date=date.today(),
            cycles=[cycle])

        site = models.Site(name=u'ucsd', title=u'UCSD')

        t_a = date.today() + timedelta(days=5)
        patient_a = models.Patient(site=site, pid=u'12345')
        visit_a = models.Visit(
            patient=patient_a, cycles=[cycle], visit_date=t_a)

        dbsession.add_all([schema, visit_a, study])
        dbsession.flush()

        req.json_body = {
            'schema': schema.id,
        }

        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(visit_a['forms'], req)

        assert 'is not part of the studies' in \
            excinfo.value.json['errors']['schema']
