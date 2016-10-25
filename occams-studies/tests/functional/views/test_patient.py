import pytest
from occams.testing import USERID, make_environ, get_csrf_token


class TestPermissionsPatientList:

    url = '/studies/patients'

    @pytest.fixture(autouse=True)
    def populate(self, app, db_session):
        from datetime import date

        import transaction
        from occams_studies import models as studies
        from occams_datastore import models as datastore

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            db_session.info['blame'] = user
            db_session.add(user)
            db_session.flush()
            db_session.add(studies.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today()))
            db_session.flush()

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer',
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member'])
    def test_allowed(self, app, db_session, group):
        environ = make_environ(userid=USERID, groups=[group])
        res = app.get(self.url, extra_environ=environ)
        assert 200 == res.status_code

    def test_not_authenticated(self, app, db_session):
        app.get(self.url, status=401)


class TestPermissionsPatientAdd:

    url = '/studies/patients'

    @pytest.fixture(autouse=True)
    def populate(self, app, db_session):
        import transaction
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            db_session.info['blame'] = user
            db_session.add(user)
            db_session.flush()
            db_session.add(studies.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today()))
            db_session.flush()

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer'])
    def test_allowed(self, app, db_session, group):
        from occams_studies import models as studies

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        site = db_session.query(studies.Site).filter(
            studies.Site.name == u'UCSD').one()
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
    def test_not_allowed(self, app, db_session, group):
        from occams_studies import models as studies

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        site = db_session.query(studies.Site).filter(
            studies.Site.name == u'UCSD').one()
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

    def test_not_authenticated(self, app, db_session):
        app.post(self.url, status=401)


class TestPermissionsPatientView:

    url = '/studies/patients/{}'

    @pytest.fixture(autouse=True)
    def populate(self, app, db_session):
        import transaction
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            db_session.info['blame'] = user
            db_session.add(user)
            db_session.flush()
            site = studies.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            db_session.add(studies.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            ))

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer',
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member'])
    def test_allowed(self, app, db_session, group):
        environ = make_environ(userid=USERID, groups=[group])
        res = app.get(
            self.url.format('123'), extra_environ=environ, status='*')

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCLA:coordinator', 'UCLA:enterer', 'UCLA:reviewer',
        'UCLA:consumer', 'UCLA:member'])
    def test_not_allowed(self, app, db_session, group):
        environ = make_environ(userid=USERID, groups=[group])
        res = app.get(
            self.url.format('123'), extra_environ=environ, status='*')

        assert 403 == res.status_code

    def test_not_authenticated(self, app, db_session):
        app.get(self.url.format('123'), status=401)


class TestPermissionsPatientDelete:

    url = '/studies/patients/{}'

    @pytest.fixture(autouse=True)
    def populate(self, app, db_session):
        import transaction
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            db_session.info['blame'] = user
            db_session.add(user)
            db_session.flush()
            site = studies.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            db_session.add(studies.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            ))

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator'])
    def test_allowed(self, app, db_session, group):
        from occams_studies import models as studies

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        patient = db_session.query(studies.Patient).filter(
            studies.Patient.pid == u'123').one()

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
    def test_not_allowed(self, app, db_session, group):
        from occams_studies import models as studies

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        patient = db_session.query(studies.Patient).filter(
            studies.Patient.pid == u'123').one()
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

    def test_not_authenticated(self, app, db_session):
        app.delete(self.url.format('123'), status=401, xhr=True)


class TestPermissionsPatientEdit:

    url = '/studies/patients/{}'

    @pytest.fixture(autouse=True)
    def populate(self, app, db_session):
        import transaction
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            db_session.info['blame'] = user
            db_session.add(user)
            db_session.flush()
            site = studies.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            db_session.add(studies.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            ))

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer'])
    def test_allowed(self, app, db_session, group):
        from occams_studies import models as studies

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        patient = db_session.query(studies.Patient).filter(
            studies.Patient.pid == u'123').one()
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
    def test_not_allowed(self, app, db_session, group):
        from occams_studies import models as studies

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        patient = db_session.query(studies.Patient).filter(
            studies.Patient.pid == u'123').one()
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

    def test_not_authenticated(self, app, db_session):
        app.put(self.url.format('123'), status=401, xhr=True)


class TestPermissionsPatientViewDiffSite:

    url = '/studies/patients/123'

    @pytest.fixture(autouse=True)
    def populate(self, app, db_session):
        import transaction
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            db_session.info['blame'] = user
            db_session.add(user)
            db_session.flush()
            site = studies.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            db_session.add(studies.Site(
                name=u'UCLA',
                title=u'UCLA',
                description=u'UCLA Campus',
                create_date=date.today()))

            db_session.add(studies.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            ))

            db_session.flush()

    @pytest.mark.parametrize('group', ['UCLA:member'])
    def test_not_allowed(self, app, db_session, group):
        environ = make_environ(userid=USERID, groups=[group])
        res = app.get(
            self.url.format('123'), extra_environ=environ, status='*')

        assert 403 == res.status_code


class TestPermissionsPatientFormsView:

    url = '/studies/patients/123/forms'

    @pytest.fixture(autouse=True)
    def populate(self, app, db_session):
        import transaction
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            db_session.info['blame'] = user
            db_session.add(user)
            db_session.flush()
            site = studies.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            db_session.add(studies.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            ))

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer',
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member'])
    def test_allowed(self, app, db_session, group):
        environ = make_environ(userid=USERID, groups=[group])
        res = app.get(self.url, extra_environ=environ, status='*')

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCLA:coordinator', 'UCLA:enterer', 'UCLA:reviewer',
        'UCLA:consumer', 'UCLA:member'])
    def test_not_allowed(self, app, db_session, group):
        environ = make_environ(userid=USERID, groups=[group])
        res = app.get(self.url, extra_environ=environ, status='*')

        assert 403 == res.status_code

    def test_not_authenticated(self, app, db_session):
        app.get(self.url.format('123'), status=401)


class TestPermissionsPatientFormsAdd:

    url = '/studies/patients/123/forms'

    @pytest.fixture(autouse=True)
    def populate(self, app, db_session):
        import transaction
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            db_session.info['blame'] = user
            db_session.add(user)
            db_session.flush()
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
                schemata=set([form])
            )

            db_session.add(studies.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            ))

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer'])
    def test_allowed(self, app, db_session, group):
        from occams_datastore import models as datastore

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        schema = db_session.query(datastore.Schema).filter(
            datastore.Schema.name == u'test_schema').one()
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
    def test_not_allowed(self, app, db_session, group):
        from occams_datastore import models as datastore

        environ = make_environ(userid=USERID, groups=[group])
        csrf_token = get_csrf_token(app, environ)

        schema = db_session.query(datastore.Schema).filter(
            datastore.Schema.name == u'test_schema').one()
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

    def test_not_authenticated(self, app, db_session):
        app.post(self.url.format('123'), status=401)


class TestPermissionsPatientFormsDelete:

    url = '/studies/patients/123/forms'

    @pytest.fixture(autouse=True)
    def populate(self, app, db_session):
        import transaction
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            db_session.info['blame'] = user
            db_session.add(user)
            db_session.flush()
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
                schemata=set([form])
            )

            db_session.add(studies.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            ))

            entity = datastore.Entity(schema=form)
            db_session.add(entity)
            db_session.flush()
            self.entity_id = entity.id

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator'])
    def test_allowed(self, app, db_session, group):

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
    def test_not_allowed(self, app, db_session, group):

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

    def test_not_authenticated(self, app, db_session):
        app.delete(self.url, status=401)


class TestPermissionsPatientFormView:

    url = '/studies/patients/123/forms/{}'

    @pytest.fixture(autouse=True)
    def populate(self, app, db_session):
        import transaction
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            db_session.info['blame'] = user
            db_session.add(user)
            db_session.flush()
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
                schemata=set([form])
            )

            state = (
                db_session.query(datastore.State)
                .filter_by(name=u'pending-entry')
                .one())

            db_session.add(datastore.Entity(
                state=state,
                schema=form,
                collect_date=date(2015, 2, 1)
            ))

            db_session.add(studies.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            ))

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer',
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member'])
    def test_allowed(self, app, db_session, group):
        from occams_datastore import models as datastore

        environ = make_environ(userid=USERID, groups=[group])
        entity_id = db_session.query(datastore.Entity.id).filter(
            datastore.Entity.schema.has(name=u'test_schema')).scalar()
        res = app.get(
            self.url.format(entity_id), extra_environ=environ)

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCLA:coordinator', 'UCLA:enterer',
        'UCLA:reviewer', 'UCLA:consumer', 'UCLA:member'])
    def test_not_allowed(self, app, db_session, group):
        from occams_datastore import models as datastore

        environ = make_environ(userid=USERID, groups=[group])
        entity_id = db_session.query(datastore.Entity.id).filter(
            datastore.Entity.schema.has(name=u'test_schema')).scalar()
        res = app.get(
            self.url.format(entity_id), extra_environ=environ, status='*')

        assert 403 == res.status_code

    def test_not_authenticated(self, app, db_session):
        from occams_datastore import models as datastore
        entity_id = db_session.query(datastore.Entity.id).filter(
            datastore.Entity.schema.has(name=u'test_schema')).scalar()

        app.get(self.url.format(entity_id), status=401)


class TestPermissionsPatientFormsEdit:

    url = '/studies/patients/123/forms/{}'

    @pytest.fixture(autouse=True)
    def populate(self, app, db_session):
        import transaction
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            db_session.info['blame'] = user
            db_session.add(user)
            db_session.flush()
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
                schemata=set([form])
            )

            state = (
                db_session.query(datastore.State)
                .filter_by(name=u'pending-entry')
                .one())

            db_session.add(datastore.Entity(
                state=state,
                schema=form,
                collect_date=date(2015, 2, 1)
            ))

            db_session.add(studies.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            ))

    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'UCSD:coordinator', 'UCSD:enterer'])
    def test_allowed(self, app, db_session, group):
        from occams_datastore import models as datastore

        environ = make_environ(userid=USERID, groups=[group])
        entity_id = db_session.query(datastore.Entity.id).filter(
            datastore.Entity.schema.has(name=u'test_schema')).scalar()
        res = app.post(
            self.url.format(entity_id), extra_environ=environ,
            params={'id_1': entity_id})

        assert 200 == res.status_code

    @pytest.mark.parametrize('group', [
        'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member',
        'UCLA:coordinator', 'UCLA:enterer', 'UCLA:enterer', None])
    def test_not_allowed(self, app, db_session, group):
        from occams_datastore import models as datastore

        environ = make_environ(userid=USERID, groups=[group])
        entity_id = db_session.query(datastore.Entity.id).filter(
            datastore.Entity.schema.has(name=u'test_schema')).scalar()
        res = app.post(
            self.url.format(entity_id), extra_environ=environ,
            params={'id_1': entity_id}, status='*')

        assert 403 == res.status_code

    def test_not_authenticated(self, app, db_session):
        from occams_datastore import models as datastore
        entity_id = db_session.query(datastore.Entity.id).filter(
            datastore.Entity.schema.has(name=u'test_schema')).scalar()

        app.post(self.url.format(entity_id), status=401)
