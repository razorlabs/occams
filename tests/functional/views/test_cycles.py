from ddt import ddt, data

from tests import FunctionalFixture, USERID


@ddt
class TestPermissionsCyclesAdd(FunctionalFixture):

    url = '/studies/{}/cycles'

    def setUp(self):
        super(TestPermissionsCyclesAdd, self).setUp()

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

            study = studies.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
                start_date=date(2014, 12, 12)
            )

            Session.add(study)
            Session.add(patient)

    @data('administrator', 'manager')
    def test_allowed(self, group):
        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get('/studies',
                                extra_environ=environ)

        data = {
            'title': 'test_study Week 1',
            'week': '1'
        }

        csrf_token = self.app.cookies['csrf_token']
        response = self.app.post_json(
            self.url.format('test_study'),
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
        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get('/studies',
                                extra_environ=environ)

        data = {
            'title': 'test_study Week 1',
            'week': '1'
        }

        csrf_token = self.app.cookies['csrf_token']
        response = self.app.post_json(
            self.url.format('test_study'),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        self.assertEquals(403, response.status_code)

    def test_not_authenticated(self):
        self.app.post(self.url.format('test_study'), status=401, xhr=True)


@ddt
class TestPermissionsCyclesDelete(FunctionalFixture):

    url = '/studies/test_study/cycles/TestDelete'

    def setUp(self):
        super(TestPermissionsCyclesDelete, self).setUp()

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

            study = studies.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
                start_date=date(2014, 12, 12)
            )

            cycle = studies.Cycle(
                name=u'TestDelete',
                title=u'TestDelete',
                week=39,
                study=study
            )

            Session.add(study)
            Session.add(patient)
            Session.add(cycle)

    @data('administrator', 'manager')
    def test_allowed(self, group):
        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get('/studies',
                                extra_environ=environ)

        csrf_token = self.app.cookies['csrf_token']
        response = self.app.delete(
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

    @data('UCSD:enterer', 'UCSD:reviewer', 'UCSD:consumer',
          'UCSD:member', None)
    def test_not_allowed(self, group):
        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get('/studies',
                                extra_environ=environ)

        csrf_token = self.app.cookies['csrf_token']
        response = self.app.delete(
            self.url,
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
        self.app.delete(self.url, status=401, xhr=True)


@ddt
class TestPermissionsCyclesEdit(FunctionalFixture):

    url = '/studies/test_study/cycles/TestDelete'

    def setUp(self):
        super(TestPermissionsCyclesEdit, self).setUp()

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

            study = studies.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
                start_date=date(2014, 12, 12)
            )

            cycle = studies.Cycle(
                name=u'TestDelete',
                title=u'TestDelete',
                week=39,
                study=study
            )

            Session.add(study)
            Session.add(patient)
            Session.add(cycle)

    @data('administrator', 'manager')
    def test_allowed(self, group):
        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get('/studies',
                                extra_environ=environ)

        data = {
            'name': 'TestDelete',
            'title': 'TestDelete',
            'week': 4
        }

        csrf_token = self.app.cookies['csrf_token']
        response = self.app.put_json(
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
        environ = self.make_environ(userid=USERID, groups=[group])
        response = self.app.get('/studies',
                                extra_environ=environ)

        data = {
            'name': 'TestDelete',
            'title': 'TestDelete',
            'week': 4
        }

        csrf_token = self.app.cookies['csrf_token']
        response = self.app.put_json(
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
        self.app.put(self.url, status=401, xhr=True)


@ddt
class TestPermissionsCyclesView(FunctionalFixture):

    url = '/studies/test_study/cycles/TestView'

    def setUp(self):
        super(TestPermissionsCyclesView, self).setUp()

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

            study = studies.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
                start_date=date(2014, 12, 12)
            )

            cycle = studies.Cycle(
                name=u'TestView',
                title=u'TestView',
                week=39,
                study=study
            )

            Session.add(study)
            Session.add(patient)
            Session.add(cycle)

    @data('administrator', 'manager', 'enterer',
          'reviewer', 'consumer', 'member')
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
