
from ddt import ddt, data

from tests import FunctionalFixture, USERID


@ddt
class TestPermissionsVisitsView(FunctionalFixture):

    url = '/studies/patients/123/visits'

    def setUp(self):
        super(TestPermissionsVisitsView, self).setUp()

        import transaction
        from occams import Session
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            Session.info['blame'] = user
            Session.add(user)
            Session.flush()

            site = studies.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            patient = studies.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            )

            form = datastore.Schema(
                name=u'test_schema',
                title=u'test_title',
                publish_date=date(2015, 1, 1)
            )

            form.attributes['termination_date'] = studies.Attribute(
                name=u'termination_date',
                title=u'termination_date',
                type=u'datetime',
                order=0
            )

            study = studies.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
                start_date=date(2014, 12, 12),
                termination_schema=form
            )

            Session.add(studies.State(
                name=u'pending-entry',
                title=u'pending-entry'
            ))

            Session.add(study)
            Session.add(patient)

    @data('administrator', 'manager', 'UCSD:enterer',
          'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member')
    def test_allowed(self, group):
        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get('/studies',
                                extra_environ=environ)

        csrf_token = self.app.cookies['csrf_token']
        response = self.app.get(
            self.url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True,
            params={})

        self.assertEquals(200, response.status_code)

    def test_not_authenticated(self):
        self.app.get(self.url, status=401, xhr=True)


@ddt
class TestPermissionsVisitsAdd(FunctionalFixture):

    url = '/studies/patients/123/visits'

    def setUp(self):
        super(TestPermissionsVisitsAdd, self).setUp()

        import transaction
        from occams import Session
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            Session.info['blame'] = user
            Session.add(user)
            Session.flush()

            site = studies.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            patient = studies.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            )

            form = datastore.Schema(
                name=u'test_schema',
                title=u'test_title',
                publish_date=date(2015, 1, 1)
            )

            form.attributes['termination_date'] = studies.Attribute(
                name=u'termination_date',
                title=u'termination_date',
                type=u'datetime',
                order=0
            )

            study = studies.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
                start_date=date(2014, 12, 12),
                termination_schema=form
            )

            cycle = studies.Cycle(
                name=u'TestCycle',
                title=u'TestCycle',
                week=39,
                study=study
            )

            Session.add(studies.State(
                name=u'pending-entry',
                title=u'pending-entry'
            ))

            Session.add(study)
            Session.add(patient)
            Session.add(cycle)

    @data('administrator', 'manager', 'UCSD:enterer')
    def test_allowed(self, group):
        from occams import Session
        from occams_studies import models as studies

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get('/studies',
                                extra_environ=environ)

        cycle_id = Session.query(studies.Cycle.id).filter(
            studies.Cycle.name == u'TestCycle').scalar()

        data = {
            'cycles': [cycle_id],
            'visit_date': '2015-01-01',
            'include_forms': False,
            'include_speciman': False
        }

        csrf_token = self.app.cookies['csrf_token']
        response = self.app.post_json(
            self.url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        self.assertEquals(200, response.status_code)

    @data('UCSD:reviewer', 'UCSD:consumer', 'UCSD:member')
    def test_not_allowed(self, group):
        from occams import Session
        from occams_studies import models as studies

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get('/studies',
                                extra_environ=environ)

        cycle_id = Session.query(studies.Cycle.id).filter(
            studies.Cycle.name == u'TestCycle').scalar()

        data = {
            'cycles': [cycle_id],
            'visit_date': '2015-01-01',
            'include_forms': False,
            'include_speciman': False
        }

        csrf_token = self.app.cookies['csrf_token']
        response = self.app.post_json(
            self.url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        self.assertEquals(403, response.status_code)

    def test_not_authenticated(self):
        self.app.post(self.url, status=401, xhr=True)


@ddt
class TestPermissionsVisitView(FunctionalFixture):

    url = '/studies/patients/123/visits/{}'

    def setUp(self):
        super(TestPermissionsVisitView, self).setUp()

        import transaction
        from occams import Session
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            Session.info['blame'] = user
            Session.add(user)
            Session.flush()

            site = studies.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            patient = studies.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            )

            form = datastore.Schema(
                name=u'test_schema',
                title=u'test_title',
                publish_date=date(2015, 1, 1)
            )

            form.attributes['termination_date'] = studies.Attribute(
                name=u'termination_date',
                title=u'termination_date',
                type=u'datetime',
                order=0
            )

            study = studies.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
                start_date=date(2014, 12, 12),
                termination_schema=form
            )

            cycle = studies.Cycle(
                name=u'TestCycle',
                title=u'TestCycle',
                week=39,
                study=study
            )

            visit = studies.Visit(
                patient=patient,
                cycles=[cycle],
                visit_date='2015-01-01'
            )

            Session.add(studies.State(
                name=u'pending-entry',
                title=u'pending-entry'
            ))

            Session.add(study)
            Session.add(patient)
            Session.add(visit)

    @data('administrator', 'manager', 'UCSD:enterer', 'UCSD:reviewer',
          'UCSD:consumer', 'UCSD:member')
    def test_allowed(self, group):
        from occams import Session
        from occams_studies import models as studies

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get('/studies',
                                extra_environ=environ)

        visit_date = Session.query(studies.Visit.visit_date).filter(
            studies.Patient.pid == u'123').scalar()

        csrf_token = self.app.cookies['csrf_token']
        response = self.app.get(
            self.url.format(visit_date),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True,
            params={})

        self.assertEquals(200, response.status_code)

    def test_not_authenticated(self):
        from occams import Session
        from occams_studies import models as studies

        visit_date = Session.query(studies.Visit.visit_date).filter(
            studies.Patient.pid == u'123').scalar()
        self.app.post(self.url.format(visit_date), status=401, xhr=True)


@ddt
class TestPermissionsVisitDelete(FunctionalFixture):

    url = '/studies/patients/123/visits/{}'

    def setUp(self):
        super(TestPermissionsVisitDelete, self).setUp()

        import transaction
        from occams import Session
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            Session.info['blame'] = user
            Session.add(user)
            Session.flush()

            site = studies.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            patient = studies.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            )

            form = datastore.Schema(
                name=u'test_schema',
                title=u'test_title',
                publish_date=date(2015, 1, 1)
            )

            form.attributes['termination_date'] = studies.Attribute(
                name=u'termination_date',
                title=u'termination_date',
                type=u'datetime',
                order=0
            )

            study = studies.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
                start_date=date(2014, 12, 12),
                termination_schema=form
            )

            cycle = studies.Cycle(
                name=u'TestCycle',
                title=u'TestCycle',
                week=39,
                study=study
            )

            visit = studies.Visit(
                patient=patient,
                cycles=[cycle],
                visit_date='2015-01-01'
            )

            Session.add(studies.State(
                name=u'pending-entry',
                title=u'pending-entry'
            ))

            Session.add(study)
            Session.add(patient)
            Session.add(visit)

    @data('administrator', 'manager')
    def test_allowed(self, group):
        from occams import Session
        from occams_studies import models as studies

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get('/studies',
                                extra_environ=environ)

        visit_date = Session.query(studies.Visit.visit_date).filter(
            studies.Patient.pid == u'123').scalar()

        csrf_token = self.app.cookies['csrf_token']
        response = self.app.delete(
            self.url.format(visit_date),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True,
            params={})

        self.assertEquals(200, response.status_code)

    @data('UCSD:enterer', 'UCSD:reviewer',
          'UCSD:consumer', 'UCSD:member')
    def test_not_allowed(self, group):
        from occams import Session
        from occams_studies import models as studies

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get('/studies',
                                extra_environ=environ)

        visit_date = Session.query(studies.Visit.visit_date).filter(
            studies.Patient.pid == u'123').scalar()

        csrf_token = self.app.cookies['csrf_token']
        response = self.app.delete(
            self.url.format(visit_date),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            xhr=True,
            params={})

        self.assertEquals(403, response.status_code)

    def test_not_authenticated(self):
        from occams import Session
        from occams_studies import models as studies

        visit_date = Session.query(studies.Visit.visit_date).filter(
            studies.Patient.pid == u'123').scalar()
        self.app.delete(self.url.format(visit_date), status=401, xhr=True)


@ddt
class TestPermissionsVisitEdit(FunctionalFixture):

    url = '/studies/patients/123/visits/{}'

    def setUp(self):
        super(TestPermissionsVisitEdit, self).setUp()

        import transaction
        from occams import Session
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            Session.info['blame'] = user
            Session.add(user)
            Session.flush()

            site = studies.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            patient = studies.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            )

            form = datastore.Schema(
                name=u'test_schema',
                title=u'test_title',
                publish_date=date(2015, 1, 1)
            )

            form.attributes['termination_date'] = studies.Attribute(
                name=u'termination_date',
                title=u'termination_date',
                type=u'datetime',
                order=0
            )

            study = studies.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
                start_date=date(2014, 12, 12),
                termination_schema=form
            )

            cycle = studies.Cycle(
                name=u'TestCycle',
                title=u'TestCycle',
                week=39,
                study=study
            )

            visit = studies.Visit(
                patient=patient,
                cycles=[cycle],
                visit_date='2015-01-01'
            )

            Session.add(studies.State(
                name=u'pending-entry',
                title=u'pending-entry'
            ))

            Session.add(study)
            Session.add(patient)
            Session.add(visit)

    @data('administrator', 'manager', 'UCSD:enterer')
    def test_allowed(self, group):
        from occams import Session
        from occams_studies import models as studies

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get('/studies',
                                extra_environ=environ)

        visit_date = Session.query(studies.Visit.visit_date).filter(
            studies.Patient.pid == u'123').scalar()

        cycle_id = Session.query(studies.Cycle.id).filter(
            studies.Cycle.name == u'TestCycle').scalar()

        data = {
            'cycles': [cycle_id],
            'visit_date': '2015-01-02'
        }

        csrf_token = self.app.cookies['csrf_token']
        response = self.app.put_json(
            self.url.format(visit_date),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        self.assertEquals(200, response.status_code)

    @data('UCSD:reviewer', 'UCSD:consumer', 'UCSD:member')
    def test_not_allowed(self, group):
        from occams import Session
        from occams_studies import models as studies

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get('/studies',
                                extra_environ=environ)

        visit_date = Session.query(studies.Visit.visit_date).filter(
            studies.Patient.pid == u'123').scalar()

        cycle_id = Session.query(studies.Cycle.id).filter(
            studies.Cycle.name == u'TestCycle').scalar()

        data = {
            'cycles': [cycle_id],
            'visit_date': '2015-01-02'
        }

        csrf_token = self.app.cookies['csrf_token']
        response = self.app.put_json(
            self.url.format(visit_date),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        self.assertEquals(403, response.status_code)

    def test_not_authenticated(self):
        from occams import Session
        from occams_studies import models as studies

        visit_date = Session.query(studies.Visit.visit_date).filter(
            studies.Patient.pid == u'123').scalar()
        self.app.put(self.url.format(visit_date), status=401, xhr=True)
