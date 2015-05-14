from ddt import ddt, data

from tests import FunctionalFixture, USERID


@ddt
class TestPermissionsPatientList(FunctionalFixture):

    url = '/studies/patients'

    def setUp(self):
        super(TestPermissionsPatientList, self).setUp()

        from datetime import date

        import transaction
        from occams import Session
        from occams_studies import models as studies
        from occams_datastore import models as datastore

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            Session.info['blame'] = user
            Session.add(user)
            Session.flush()
            Session.add(studies.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today()))
            Session.flush()

    @data('administrator', 'manager', 'UCSD:enterer', 'UCSD:reviewer',
          'UCSD:consumer', 'UCSD:member')
    def test_allowed(self, group):
        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get(self.url, extra_environ=environ)
        self.assertEquals(200, response.status_code)

    def test_not_authenticated(self):
        self.app.get(self.url, status=401)


@ddt
class TestPermissionsPatientAdd(FunctionalFixture):

    url = '/studies/patients'

    def setUp(self):
        super(TestPermissionsPatientAdd, self).setUp()

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
            Session.add(studies.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today()))
            Session.flush()

    @data('administrator', 'manager', 'UCSD:enterer')
    def test_allowed(self, group):
        from occams import Session
        from occams_studies import models as studies

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get(self.url, extra_environ=environ, xhr=True)
        site = Session.query(studies.Site).filter(
            studies.Site.name == u'UCSD').one()
        site_id = site.id
        data = {
            'site': site_id,
            'references': [],
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

    @data('UCSD:reviewer', 'UCSD:consumer', 'UCSD:member',
          'UCLA:enterer', None)
    def test_not_allowed(self, group):
        from occams import Session
        from occams_studies import models as studies

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get('/studies', extra_environ=environ, xhr=True)
        site = Session.query(studies.Site).filter(
            studies.Site.name == u'UCSD').one()
        site_id = site.id

        data = {
            'site': site_id,
            'references': []
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
        self.app.post(self.url, status=401)


@ddt
class TestPermissionsPatientView(FunctionalFixture):

    url = '/studies/patients/{}'

    def setUp(self):
        super(TestPermissionsPatientView, self).setUp()

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

            Session.add(studies.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            ))

    @data('administrator', 'manager', 'UCSD:enterer', 'UCSD:reviewer',
          'UCSD:consumer', 'UCSD:member')
    def test_allowed(self, group):
        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get(
            self.url.format('123'), extra_environ=environ, status='*')

        self.assertEquals(200, response.status_code)

    @data('UCLA:enterer', 'UCLA:reviewer',
          'UCLA:consumer', 'UCLA:member')
    def test_not_allowed(self, group):
        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get(
            self.url.format('123'), extra_environ=environ, status='*')

        self.assertEquals(403, response.status_code)

    def test_not_authenticated(self):
        self.app.get(self.url.format('123'), status=401)


@ddt
class TestPermissionsPatientDelete(FunctionalFixture):

    url = '/studies/patients/{}'

    def setUp(self):
        super(TestPermissionsPatientDelete, self).setUp()

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

            Session.add(studies.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            ))

    @data('administrator', 'manager')
    def test_allowed(self, group):
        from occams import Session
        from occams_studies import models as studies

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get(self.url.format('123'), extra_environ=environ)
        csrf_token = self.app.cookies['csrf_token']

        patient = Session.query(studies.Patient).filter(
            studies.Patient.pid == u'123').one()
        data = {
            'initials': patient.initials,
            'nurse': patient.nurse,
            'site_id': patient.site_id,
            'pid': patient.pid
        }

        response = self.app.delete_json(
            self.url.format('123'),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        self.assertEquals(200, response.status_code)

    @data('UCSD:enterer', 'UCSD:reviewer', 'UCSD:consumer',
          'UCSD:member', None)
    def test_not_allowed(self, group):
        from occams import Session
        from occams_studies import models as studies

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get('/studies', extra_environ=environ, status='*')
        csrf_token = self.app.cookies['csrf_token']

        patient = Session.query(studies.Patient).filter(
            studies.Patient.pid == u'123').one()
        data = {
            'initials': patient.initials,
            'nurse': patient.nurse,
            'site_id': patient.site_id,
            'pid': patient.pid
        }

        response = self.app.delete_json(
            self.url.format('123'),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        self.assertEquals(403, response.status_code)

    def test_not_authenticated(self):
        self.app.delete(self.url.format('123'), status=401, xhr=True)


@ddt
class TestPermissionsPatientEdit(FunctionalFixture):

    url = '/studies/patients/{}'

    def setUp(self):
        super(TestPermissionsPatientEdit, self).setUp()

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

            Session.add(studies.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            ))

    @data('administrator', 'manager', 'UCSD:enterer')
    def test_allowed(self, group):
        from occams import Session
        from occams_studies import models as studies

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get(self.url.format('123'), extra_environ=environ)
        csrf_token = self.app.cookies['csrf_token']

        patient = Session.query(studies.Patient).filter(
            studies.Patient.pid == u'123').one()
        data = {
            'initials': patient.initials,
            'nurse': patient.nurse,
            'site_id': patient.site_id,
            'pid': patient.pid,
            'site': patient.site_id
        }

        response = self.app.put_json(
            self.url.format('123'),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        self.assertEquals(200, response.status_code)

    @data('UCSD:reviewer', 'UCSD:consumer', 'UCSD:member',
          'UCLA:enterer',  None)
    def test_not_allowed(self, group):
        from occams import Session
        from occams_studies import models as studies

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get('/studies', extra_environ=environ, status='*')
        csrf_token = self.app.cookies['csrf_token']

        patient = Session.query(studies.Patient).filter(
            studies.Patient.pid == u'123').one()
        data = {
            'initials': patient.initials,
            'nurse': patient.nurse,
            'site_id': patient.site_id,
            'pid': patient.pid,
            'site': patient.site_id
        }

        response = self.app.put_json(
            self.url.format('123'),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        self.assertEquals(403, response.status_code)

    def test_not_authenticated(self):
        self.app.put(self.url.format('123'), status=401, xhr=True)


@ddt
class TestPermissionsPatientViewDiffSite(FunctionalFixture):

    url = '/studies/patients/123'

    def setUp(self):
        super(TestPermissionsPatientViewDiffSite, self).setUp()

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

            Session.add(studies.Site(
                name=u'UCLA',
                title=u'UCLA',
                description=u'UCLA Campus',
                create_date=date.today()))

            Session.add(studies.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            ))

            Session.flush()

    @data('UCLA:member')
    def test_not_allowed(self, group):
        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get(
            self.url.format('123'), extra_environ=environ, status='*')

        self.assertEquals(403, response.status_code)


@ddt
class TestPermissionsPatientFormsView(FunctionalFixture):

    url = '/studies/patients/123/forms'

    def setUp(self):
        super(TestPermissionsPatientFormsView, self).setUp()

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

            Session.add(studies.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            ))

    @data('administrator', 'manager', 'UCSD:enterer', 'UCSD:reviewer',
          'UCSD:consumer', 'UCSD:member')
    def test_allowed(self, group):
        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get(self.url, extra_environ=environ, status='*')

        self.assertEquals(200, response.status_code)

    @data('UCLA:enterer', 'UCLA:reviewer',
          'UCLA:consumer', 'UCLA:member')
    def test_not_allowed(self, group):
        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get(self.url, extra_environ=environ, status='*')

        self.assertEquals(403, response.status_code)

    def test_not_authenticated(self):
        self.app.get(self.url.format('123'), status=401)


@ddt
class TestPermissionsPatientFormsAdd(FunctionalFixture):

    url = '/studies/patients/123/forms'

    def setUp(self):
        super(TestPermissionsPatientFormsAdd, self).setUp()

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

            study = studies.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
                start_date=date(2014, 12, 12),
                schemata=set([form])
            )

            Session.add(studies.State(
                name=u'pending-entry',
                title=u'pending-entry'
            ))

            Session.add(studies.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            ))

    @data('administrator', 'manager', 'UCSD:enterer')
    def test_allowed(self, group):
        from occams import Session
        from occams_datastore import models as datastore

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get('/', extra_environ=environ)
        csrf_token = self.app.cookies['csrf_token']

        schema = Session.query(datastore.Schema).filter(
            datastore.Schema.name == u'test_schema').one()
        schema_id = schema.id

        data = {
            'collect_date': '2015-01-01',
            'schema': schema_id
        }

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

    @data('UCSD:reviewer', 'UCSD:consumer', 'UCSD:member',
          'UCLA:enterer', None)
    def test_not_allowed(self, group):
        from occams import Session
        from occams_datastore import models as datastore

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get('/studies', extra_environ=environ, status='*')
        csrf_token = self.app.cookies['csrf_token']

        schema = Session.query(datastore.Schema).filter(
            datastore.Schema.name == u'test_schema').one()
        schema_id = schema.id

        data = {
            'collect_date': '2015-01-01',
            'schema': schema_id
        }

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
        self.app.post(self.url.format('123'), status=401)


@ddt
class TestPermissionsPatientFormsDelete(FunctionalFixture):

    url = '/studies/patients/123/forms'

    def setUp(self):
        super(TestPermissionsPatientFormsDelete, self).setUp()

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

            study = studies.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
                start_date=date(2014, 12, 12),
                schemata=set([form])
            )

            Session.add(studies.State(
                name=u'pending-entry',
                title=u'pending-entry'
            ))

            Session.add(studies.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            ))

    @data('administrator', 'manager')
    def test_allowed(self, group):
        from occams import Session
        from occams_datastore import models as datastore

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get(self.url, extra_environ=environ)
        csrf_token = self.app.cookies['csrf_token']

        schema = Session.query(datastore.Schema).filter(
            datastore.Schema.name == u'test_schema').one()
        schema_id = schema.id

        data = {
            'forms': schema_id
        }

        response = self.app.delete_json(
            self.url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        self.assertEquals(200, response.status_code)

    @data('UCSD:enterer', 'UCSD:reviewer', 'UCSD:consumer',
          'UCSD:member', None)
    def test_not_allowed(self, group):
        from occams import Session
        from occams_datastore import models as datastore

        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get('/studies', extra_environ=environ, status='*')
        csrf_token = self.app.cookies['csrf_token']

        schema = Session.query(datastore.Schema).filter(
            datastore.Schema.name == u'test_schema').one()
        schema_id = schema.id

        data = {
            'forms': schema_id
        }

        response = self.app.delete_json(
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
        self.app.delete(self.url, status=401)


@ddt
class TestPermissionsPatientFormView(FunctionalFixture):

    url = '/studies/patients/123/forms/{}'

    def setUp(self):
        super(TestPermissionsPatientFormView, self).setUp()

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

            study = studies.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
                start_date=date(2014, 12, 12),
                schemata=set([form])
            )

            state = studies.State(
                name=u'pending-entry',
                title=u'pending-entry'
            )

            Session.add(datastore.Entity(
                state=state,
                schema=form,
                collect_date=date(2015, 02, 1)
            ))

            Session.add(studies.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            ))

    @data('administrator', 'manager', 'UCSD:enterer',
          'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member')
    def test_allowed(self, group):
        from occams import Session
        from occams_datastore import models as datastore

        environ = self.make_environ(userid=USERID, groups=[group])
        entity_id = Session.query(datastore.Entity.id).filter(
            datastore.Entity.schema.has(name=u'test_schema')).scalar()
        response = self.app.get(
            self.url.format(entity_id), extra_environ=environ)

        self.assertEquals(200, response.status_code)

    @data('UCLA:enterer', 'UCLA:reviewer',
          'UCLA:consumer', 'UCLA:member')
    def test_not_allowed(self, group):
        from occams import Session
        from occams_datastore import models as datastore

        environ = self.make_environ(userid=USERID, groups=[group])
        entity_id = Session.query(datastore.Entity.id).filter(
            datastore.Entity.schema.has(name=u'test_schema')).scalar()
        response = self.app.get(
            self.url.format(entity_id), extra_environ=environ, status='*')

        self.assertEquals(403, response.status_code)

    def test_not_authenticated(self):
        from occams import Session
        from occams_datastore import models as datastore
        entity_id = Session.query(datastore.Entity.id).filter(
            datastore.Entity.schema.has(name=u'test_schema')).scalar()

        self.app.get(self.url.format(entity_id), status=401)


@ddt
class TestPermissionsPatientFormsEdit(FunctionalFixture):

    url = '/studies/patients/123/forms/{}'

    def setUp(self):
        super(TestPermissionsPatientFormsEdit, self).setUp()

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

            study = studies.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
                start_date=date(2014, 12, 12),
                schemata=set([form])
            )

            state = studies.State(
                name=u'pending-entry',
                title=u'pending-entry'
            )

            Session.add(datastore.Entity(
                state=state,
                schema=form,
                collect_date=date(2015, 02, 1)
            ))

            Session.add(studies.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            ))

    @data('administrator', 'manager', 'UCSD:enterer')
    def test_allowed(self, group):
        from occams import Session
        from occams_datastore import models as datastore

        environ = self.make_environ(userid=USERID, groups=[group])
        entity_id = Session.query(datastore.Entity.id).filter(
            datastore.Entity.schema.has(name=u'test_schema')).scalar()
        response = self.app.post(
            self.url.format(entity_id), extra_environ=environ,
            params={'id_1': entity_id})

        self.assertEquals(200, response.status_code)

    @data('UCSD:reviewer', 'UCSD:consumer', 'UCSD:member',
          'UCLA:enterer', 'UCLA:enterer', None)
    def test_not_allowed(self, group):
        from occams import Session
        from occams_datastore import models as datastore

        environ = self.make_environ(userid=USERID, groups=[group])
        entity_id = Session.query(datastore.Entity.id).filter(
            datastore.Entity.schema.has(name=u'test_schema')).scalar()
        response = self.app.post(
            self.url.format(entity_id), extra_environ=environ,
            params={'id_1': entity_id}, status='*')

        self.assertEquals(403, response.status_code)

    def test_not_authenticated(self):
        from occams import Session
        from occams_datastore import models as datastore
        entity_id = Session.query(datastore.Entity.id).filter(
            datastore.Entity.schema.has(name=u'test_schema')).scalar()

        self.app.post(self.url.format(entity_id), status=401)
