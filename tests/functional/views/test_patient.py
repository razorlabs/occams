import pytest
from tests.testing import USERID, make_environ, get_csrf_token


class TestPermissionsPatientList:

    url = '/studies/patients'

    @pytest.fixture(autouse=True)
    def populate(self, app, dbsession):
        from datetime import date

        import transaction
        from occams import models

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = models.User(key=USERID)
            dbsession.info['blame'] = user
            dbsession.add(user)
            dbsession.flush()
            dbsession.add(models.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today()))
            dbsession.flush()

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer',
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member'])
    def test_allowed(self, app, dbsession, group):
        environ = make_environ(userid=USERID, groups=[group])
        res = app.get(self.url, extra_environ=environ)
        assert 200 == res.status_code

    def test_not_authenticated(self, app, dbsession):
        app.get(self.url, status=401)


class TestPermissionsPatientAdd:

    url = '/studies/patients'

    @pytest.fixture(autouse=True)
    def populate(self, app, dbsession):
        import transaction
        from occams import models
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = models.User(key=USERID)
            dbsession.info['blame'] = user
            dbsession.add(user)
            dbsession.flush()
            dbsession.add(models.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today()))
            dbsession.flush()

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer'])
    def test_allowed(self, app, dbsession, group):
        from occams import models

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        site = dbsession.query(models.Site).filter(
            models.Site.name == u'UCSD').one()
        site_id = site.id

        data = {
            'site': site_id,
            'references': [],
        }

        res = app.post_json(
            self.url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)
        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member',
        'UCLA:coordinator', 'UCLA:enterer', None])
    def test_not_allowed(self, app, dbsession, group):
        from occams import models

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        site = dbsession.query(models.Site).filter(
            models.Site.name == u'UCSD').one()
        site_id = site.id

        data = {
            'site': site_id,
            'references': []
        }

        res = app.post_json(
            self.url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated(self, app, dbsession):
        app.post(self.url, status=401)


class TestPermissionsPatientView:

    url = '/studies/patients/{}'

    @pytest.fixture(autouse=True)
    def populate(self, app, dbsession):
        import transaction
        from occams import models
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = models.User(key=USERID)
            dbsession.info['blame'] = user
            dbsession.add(user)
            dbsession.flush()
            site = models.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            dbsession.add(models.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            ))

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer',
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member'])
    def test_allowed(self, app, dbsession, group):
        environ = make_environ(userid=USERID, groups=[group])
        res = app.get(
            self.url.format('123'), extra_environ=environ, status='*')

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCLA:coordinator', 'UCLA:enterer', 'UCLA:reviewer',
        'UCLA:consumer', 'UCLA:member'])
    def test_not_allowed(self, app, dbsession, group):
        environ = make_environ(userid=USERID, groups=[group])
        res = app.get(
            self.url.format('123'), extra_environ=environ, status='*')

        assert 403 == res.status_code

    def test_not_authenticated(self, app, dbsession):
        app.get(self.url.format('123'), status=401)


class TestPermissionsPatientDelete:

    url = '/studies/patients/{}'

    @pytest.fixture(autouse=True)
    def populate(self, app, dbsession):
        import transaction
        from occams import models
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = models.User(key=USERID)
            dbsession.info['blame'] = user
            dbsession.add(user)
            dbsession.flush()
            site = models.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            dbsession.add(models.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            ))

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator'])
    def test_allowed(self, app, dbsession, group):
        from occams import models

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        patient = dbsession.query(models.Patient).filter(
            models.Patient.pid == u'123').one()

        data = {
            'initials': patient.initials,
            'nurse': patient.nurse,
            'site_id': patient.site_id,
            'pid': patient.pid
        }

        res = app.delete_json(
            self.url.format('123'),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCSD:enterer', 'UCSD:reviewer', 'UCSD:consumer',
        'UCSD:member', 'UCLA:coorindator', None])
    def test_not_allowed(self, app, dbsession, group):
        from occams import models

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        patient = dbsession.query(models.Patient).filter(
            models.Patient.pid == u'123').one()
        data = {
            'initials': patient.initials,
            'nurse': patient.nurse,
            'site_id': patient.site_id,
            'pid': patient.pid
        }

        res = app.delete_json(
            self.url.format('123'),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated(self, app, dbsession):
        app.delete(self.url.format('123'), status=401, xhr=True)


class TestPermissionsPatientEdit:

    url = '/studies/patients/{}'

    @pytest.fixture(autouse=True)
    def populate(self, app, dbsession):
        import transaction
        from occams import models
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = models.User(key=USERID)
            dbsession.info['blame'] = user
            dbsession.add(user)
            dbsession.flush()
            site = models.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            dbsession.add(models.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            ))

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer'])
    def test_allowed(self, app, dbsession, group):
        from occams import models

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        patient = dbsession.query(models.Patient).filter(
            models.Patient.pid == u'123').one()
        data = {
            'initials': patient.initials,
            'nurse': patient.nurse,
            'site_id': patient.site_id,
            'pid': patient.pid,
            'site': patient.site_id
        }

        res = app.put_json(
            self.url.format('123'),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member',
        'UCLA:coorindator', 'UCLA:enterer', None])
    def test_not_allowed(self, app, dbsession, group):
        from occams import models

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        patient = dbsession.query(models.Patient).filter(
            models.Patient.pid == u'123').one()
        data = {
            'initials': patient.initials,
            'nurse': patient.nurse,
            'site_id': patient.site_id,
            'pid': patient.pid,
            'site': patient.site_id
        }

        res = app.put_json(
            self.url.format('123'),
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated(self, app, dbsession):
        app.put(self.url.format('123'), status=401, xhr=True)


class TestPermissionsPatientViewDiffSite:

    url = '/studies/patients/123'

    @pytest.fixture(autouse=True)
    def populate(self, app, dbsession):
        import transaction
        from occams import models
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = models.User(key=USERID)
            dbsession.info['blame'] = user
            dbsession.add(user)
            dbsession.flush()
            site = models.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            dbsession.add(models.Site(
                name=u'UCLA',
                title=u'UCLA',
                description=u'UCLA Campus',
                create_date=date.today()))

            dbsession.add(models.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            ))

            dbsession.flush()

    @pytest.mark.parametrize('group', ['UCLA:member'])
    def test_not_allowed(self, app, dbsession, group):
        environ = make_environ(userid=USERID, groups=[group])
        res = app.get(
            self.url.format('123'), extra_environ=environ, status='*')

        assert 403 == res.status_code


class TestPermissionsPatientFormsView:

    url = '/studies/patients/123/forms'

    @pytest.fixture(autouse=True)
    def populate(self, app, dbsession):
        import transaction
        from occams import models
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = models.User(key=USERID)
            dbsession.info['blame'] = user
            dbsession.add(user)
            dbsession.flush()
            site = models.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            dbsession.add(models.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            ))

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer',
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member'])
    def test_allowed(self, app, dbsession, group):
        environ = make_environ(userid=USERID, groups=[group])
        res = app.get(self.url, extra_environ=environ, status='*')

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCLA:coordinator', 'UCLA:enterer', 'UCLA:reviewer',
        'UCLA:consumer', 'UCLA:member'])
    def test_not_allowed(self, app, dbsession, group):
        environ = make_environ(userid=USERID, groups=[group])
        res = app.get(self.url, extra_environ=environ, status='*')

        assert 403 == res.status_code

    def test_not_authenticated(self, app, dbsession):
        app.get(self.url.format('123'), status=401)


class TestPermissionsPatientFormsAdd:

    url = '/studies/patients/123/forms'

    @pytest.fixture(autouse=True)
    def populate(self, app, dbsession):
        import transaction
        from occams import models
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = models.User(key=USERID)
            dbsession.info['blame'] = user
            dbsession.add(user)
            dbsession.flush()
            site = models.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            patient = models.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            )

            form = models.Schema(
                name=u'test_schema',
                title=u'test_title',
                publish_date=date(2015, 1, 1)
            )

            study = models.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
                schemata=set([form])
            )

            dbsession.add(models.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            ))

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer'])
    def test_allowed(self, app, dbsession, group):
        from occams import models

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        schema = dbsession.query(models.Schema).filter(
            models.Schema.name == u'test_schema').one()
        schema_id = schema.id

        data = {
            'collect_date': '2015-01-01',
            'schema': schema_id
        }

        res = app.post_json(
            self.url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member',
        'UCLA:coordinator', 'UCLA:enterer', None])
    def test_not_allowed(self, app, dbsession, group):
        from occams import models

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        schema = dbsession.query(models.Schema).filter(
            models.Schema.name == u'test_schema').one()
        schema_id = schema.id

        data = {
            'collect_date': '2015-01-01',
            'schema': schema_id
        }

        res = app.post_json(
            self.url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated(self, app, dbsession):
        app.post(self.url.format('123'), status=401)


class TestPermissionsPatientFormsDelete:

    url = '/studies/patients/123/forms'

    @pytest.fixture(autouse=True)
    def populate(self, app, dbsession):
        import transaction
        from occams import models
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = models.User(key=USERID)
            dbsession.info['blame'] = user
            dbsession.add(user)
            dbsession.flush()
            site = models.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            patient = models.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            )

            form = models.Schema(
                name=u'test_schema',
                title=u'test_title',
                publish_date=date(2015, 1, 1)
            )

            study = models.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
                schemata=set([form])
            )

            dbsession.add(models.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            ))

            entity = models.Entity(schema=form)
            dbsession.add(entity)
            dbsession.flush()
            self.entity_id = entity.id

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator'])
    def test_allowed(self, app, dbsession, group):

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        data = {
            'forms': [self.entity_id]
        }

        res = app.delete_json(
            self.url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCSD:enterer', 'UCSD:reviewer', 'UCSD:consumer',
        'UCSD:member',
        'UCLA:coordinator', None])
    def test_not_allowed(self, app, dbsession, group):

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        data = {
            'forms': [self.entity_id]
        }

        res = app.delete_json(
            self.url,
            extra_environ=environ,
            status='*',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-REQUESTED-WITH': str('XMLHttpRequest')
            },
            params=data)

        assert 403 == res.status_code

    def test_not_authenticated(self, app, dbsession):
        app.delete(self.url, status=401)


class TestPermissionsPatientFormView:

    url = '/studies/patients/123/forms/{}'

    @pytest.fixture(autouse=True)
    def populate(self, app, dbsession):
        import transaction
        from occams import models
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = models.User(key=USERID)
            dbsession.info['blame'] = user
            dbsession.add(user)
            dbsession.flush()
            site = models.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            patient = models.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            )

            form = models.Schema(
                name=u'test_schema',
                title=u'test_title',
                publish_date=date(2015, 1, 1)
            )

            study = models.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
                schemata=set([form])
            )

            state = (
                dbsession.query(models.State)
                .filter_by(name=u'pending-entry')
                .one())

            dbsession.add(models.Entity(
                state=state,
                schema=form,
                collect_date=date(2015, 2, 1)
            ))

            dbsession.add(models.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            ))

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer',
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member'])
    def test_allowed(self, app, dbsession, group):
        from occams import models

        environ = make_environ(userid=USERID, groups=[group])
        entity_id = dbsession.query(models.Entity.id).filter(
            models.Entity.schema.has(name=u'test_schema')).scalar()
        res = app.get(
            self.url.format(entity_id), extra_environ=environ)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCLA:coordinator', 'UCLA:enterer',
        'UCLA:reviewer', 'UCLA:consumer', 'UCLA:member'])
    def test_not_allowed(self, app, dbsession, group):
        from occams import models

        environ = make_environ(userid=USERID, groups=[group])
        entity_id = dbsession.query(models.Entity.id).filter(
            models.Entity.schema.has(name=u'test_schema')).scalar()
        res = app.get(
            self.url.format(entity_id), extra_environ=environ, status='*')

        assert 403 == res.status_code

    def test_not_authenticated(self, app, dbsession):
        from occams import models
        entity_id = dbsession.query(models.Entity.id).filter(
            models.Entity.schema.has(name=u'test_schema')).scalar()

        app.get(self.url.format(entity_id), status=401)


class TestPermissionsPatientFormsEdit:

    url = '/studies/patients/123/forms/{}'

    @pytest.fixture(autouse=True)
    def populate(self, app, dbsession):
        import transaction
        from occams import models
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = models.User(key=USERID)
            dbsession.info['blame'] = user
            dbsession.add(user)
            dbsession.flush()
            site = models.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            patient = models.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            )

            form = models.Schema(
                name=u'test_schema',
                title=u'test_title',
                publish_date=date(2015, 1, 1)
            )

            study = models.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
                schemata=set([form])
            )

            state = (
                dbsession.query(models.State)
                .filter_by(name=u'pending-entry')
                .one())

            dbsession.add(models.Entity(
                state=state,
                schema=form,
                collect_date=date(2015, 2, 1)
            ))

            dbsession.add(models.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            ))

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer'])
    def test_allowed(self, app, dbsession, group):
        from occams import models

        environ = make_environ(userid=USERID, groups=[group])
        entity_id = dbsession.query(models.Entity.id).filter(
            models.Entity.schema.has(name=u'test_schema')).scalar()
        res = app.post(
            self.url.format(entity_id), extra_environ=environ,
            params={'id_1': entity_id})

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member',
        'UCLA:coordinator', 'UCLA:enterer', 'UCLA:enterer', None])
    def test_not_allowed(self, app, dbsession, group):
        from occams import models

        environ = make_environ(userid=USERID, groups=[group])
        entity_id = dbsession.query(models.Entity.id).filter(
            models.Entity.schema.has(name=u'test_schema')).scalar()
        res = app.post(
            self.url.format(entity_id), extra_environ=environ,
            params={'id_1': entity_id}, status='*')

        assert 403 == res.status_code

    def test_not_authenticated(self, app, dbsession):
        from occams import models
        entity_id = dbsession.query(models.Entity.id).filter(
            models.Entity.schema.has(name=u'test_schema')).scalar()

        app.post(self.url.format(entity_id), status=401)
