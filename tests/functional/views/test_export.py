import pytest
from occams.testing import USERID, make_environ, get_csrf_token


class TestPermissionsAbout:

    url = '/studies/exports'

    @pytest.fixture(autouse=True)
    def populate(self, app, dbsession):
        import transaction
        from occams_datastore import models as datastore

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            dbsession.add(datastore.User(key=USERID))

    @pytest.mark.parametrize('group', ['administrator', 'consumer'])
    def test_allowed(self, app, dbsession, group):
        environ = make_environ(userid=USERID, groups=[group])
        app.get(self.url, extra_environ=environ, status=200)

    @pytest.mark.parametrize('group', [None])
    def test_not_allowed(self, app, dbsession, group):
        environ = make_environ(userid=USERID, groups=[group])
        app.get(self.url, extra_environ=environ, status=403)

    def test_not_authenticated(self, app, dbsession):
        app.get(self.url, status=401)


class TestExportViewPermissionsFaq:

    url = '/studies/exports/faq'

    @pytest.fixture(autouse=True)
    def populate(self, app, dbsession):
        import transaction
        from occams_datastore import models as datastore

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            dbsession.add(datastore.User(key=USERID))

    @pytest.mark.parametrize('group', ['administrator', 'manager', 'consumer'])
    def test_allowed(self, app, dbsession, group):
        environ = make_environ(userid=USERID, groups=[group])
        app.get(self.url, extra_environ=environ, status=200)

    @pytest.mark.parametrize('group', [None])
    def test_not_allowed(self, app, dbsession, group):
        environ = make_environ(userid=USERID, groups=[group])
        app.get(self.url, extra_environ=environ, status=403)

    def test_not_authenticated(self, app, dbsession):
        app.get(self.url, status=401)


class TestPermissionsCheckout:

    url = '/studies/exports/checkout'

    @pytest.fixture(autouse=True)
    def populate(self, app, dbsession):
        import transaction
        from occams_datastore import models as datastore

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            dbsession.add(datastore.User(key=USERID))

    @pytest.mark.parametrize('group', ['administrator', 'manager', 'consumer'])
    def test_allowed(self, app, dbsession, group):
        environ = make_environ(userid=USERID, groups=[group])
        app.get(self.url, extra_environ=environ, status=200)

    @pytest.mark.parametrize('group', [None])
    def test_not_allowed(self, app, dbsession, group):
        environ = make_environ(userid=USERID, groups=[group])
        app.get(self.url, extra_environ=environ, status=403)

    def test_not_authenticated(self, app, dbsession):
        app.get(self.url, status=401)


class TestPermissionsStatus:

    url = '/studies/exports/status'

    @pytest.fixture(autouse=True)
    def populate(self, app, dbsession):
        import transaction
        from occams_datastore import models as datastore

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            dbsession.add(datastore.User(key=USERID))

    @pytest.mark.parametrize('group', ['administrator', 'manager', 'consumer'])
    def test_allowed(self, app, dbsession, group):
        environ = make_environ(groups=[group])
        app.get(self.url, extra_environ=environ, status=200)

    @pytest.mark.parametrize('group', [None])
    def test_not_allowed(self, app, dbsession, group):
        environ = make_environ(groups=[group])
        app.get(self.url, extra_environ=environ, status=403)

    def test_not_authenticated(self, app, dbsession):
        app.get(self.url, status=401)


class TestPermissionsStatusJSON:

    url = '/studies/exports/status'

    @pytest.fixture(autouse=True)
    def populate(self, app, dbsession):
        import transaction
        from occams_datastore import models as datastore

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            dbsession.add(datastore.User(key=USERID))

    @pytest.mark.parametrize('group', ['administrator', 'manager', 'consumer'])
    def test_allowed(self, app, dbsession, group):
        environ = make_environ(groups=[group])
        app.get(self.url, extra_environ=environ, xhr=True, status=200)

    @pytest.mark.parametrize('group', [None])
    def test_not_allowed(self, app, dbsession, group):
        environ = make_environ(groups=[group])
        app.get(self.url, extra_environ=environ, xhr=True, status=403)

    def test_not_authenticated(self, app, dbsession):
        app.get(self.url, xhr=True, status=401)


class TestPermissionsNotifications:

    url = '/studies/exports/notifications'

    @pytest.fixture(autouse=True)
    def populate(self, app, dbsession):
        import transaction
        from occams_datastore import models as datastore

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            dbsession.add(datastore.User(key=USERID))

    @pytest.mark.parametrize('group', ['administrator', 'manager', 'consumer'])
    def test_allowed(self, app, dbsession, group):
        environ = make_environ(groups=[group])
        app.get(self.url, extra_environ=environ, xhr=True, status=200)

    @pytest.mark.parametrize('group', [None])
    def test_not_allowed(self, app, dbsession, group):
        environ = make_environ(groups=[group])
        app.get(self.url, extra_environ=environ, xhr=True, status=403)

    def test_not_authenticated(self, app, dbsession):
        app.get(self.url, xhr=True, status=401)


class TestPersmissionsDelete:

    url_fmt = '/studies/exports/{export}'

    @pytest.fixture(autouse=True)
    def populate(self, app, dbsession):
        import transaction
        from occams_datastore import models as datastore
        from occams import models

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            dbsession.info['blame'] = user
            dbsession.add(user)
            export = models.Export(owner_user=user)
            dbsession.add(export)
            dbsession.flush()
            self.url = self.url_fmt.format(export=export.id)

    # None indicates current user
    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'consumer', None])
    def test_allowed(self, app, dbsession, group):
        environ = make_environ(groups=[group])
        csrf_token = get_csrf_token(app, environ)
        app.delete(
            self.url,
            extra_environ=environ,
            headers={'X-CSRF-Token': csrf_token},
            xhr=True,
            status=200)

    def test_not_owner(self, app, dbsession):
        import transaction
        from occams_datastore import models as datastore
        with transaction.manager:
            dbsession.add(datastore.User(key='somebody_else'))
        environ = make_environ(userid='somebody_else')
        csrf_token = get_csrf_token(app, environ)
        app.delete(
            self.url,
            extra_environ=environ,
            headers={'X-CSRF-Token': csrf_token},
            xhr=True,
            status=403)

    def test_not_authenticated(self, app, dbsession):
        app.delete(self.url, xhr=True, status=401)


class TestPersmissionsCodebook:

    url = '/studies/exports/codebook'

    @pytest.fixture(autouse=True)
    def populate(self, app, dbsession):
        import transaction
        from occams_datastore import models as datastore

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            dbsession.add(datastore.User(key=USERID))

    @pytest.mark.parametrize('group', ['administrator', 'manager', 'consumer'])
    def test_allowed(self, app, dbsession, group):
        environ = make_environ(groups=[group])
        app.get(self.url, extra_environ=environ, status=200)

    @pytest.mark.parametrize('group', [None])
    def test_not_allowed(self, app, dbsession, group):
        environ = make_environ(groups=[group])
        app.get(self.url, extra_environ=environ, status=403)

    def test_not_authenticated(self, app, dbsession):
        app.get(self.url, status=401)


class TestPersmissionsCodebookJSON:

    url = '/studies/exports/codebook'

    @pytest.fixture(autouse=True)
    def populate(self, app, dbsession):
        import transaction
        from occams_datastore import models as datastore

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            dbsession.add(datastore.User(key=USERID))

    @pytest.mark.parametrize('group', ['administrator', 'manager', 'consumer'])
    def test_allowed(self, app, dbsession, group):
        environ = make_environ(groups=[group])
        app.get(
            self.url,
            {'file': 'pid'},
            extra_environ=environ,
            xhr=True,
            status=200)

    @pytest.mark.parametrize('group', [None])
    def test_not_allowed(self, app, dbsession, group):
        environ = make_environ(groups=[group])
        app.get(
            self.url,
            {'file': 'pid'},
            extra_environ=environ,
            xhr=True,
            status=403)

    def test_not_authenticated(self, app, dbsession):
        app.get(self.url, status=401)


class TestPersmissionsCodebookDownload:

    url = '/studies/exports/codebook?alt=csv'

    @pytest.fixture(autouse=True)
    def populate(self, request, app, dbsession):
        import os
        import transaction
        from occams_datastore import models as datastore

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            dbsession.add(datastore.User(key=USERID))

        # XXX: need to somehow get the settings so we can consitently
        #      get the correct directory
        with open('/tmp/codebook.csv', 'w+') as fp:
            self.codebook_file_name = fp.name

        def rm():
            os.unlink(self.codebook_file_name)

        request.addfinalizer(rm)

    @pytest.mark.parametrize('group', ['administrator', 'manager', 'consumer'])
    def test_allowed(self, app, dbsession, group):
        environ = make_environ(groups=[group])
        app.get(self.url, extra_environ=environ, status=200)

    @pytest.mark.parametrize('group', [None])
    def test_not_allowed(self, app, dbsession, group):
        environ = make_environ(groups=[group])
        app.get(self.url, extra_environ=environ, status=403)

    def test_not_authenticated(self, app, dbsession):
        app.get(self.url, status=401)


class TestPermissionsDownload:

    url_fmt = '/studies/exports/{export}/download'

    @pytest.fixture(autouse=True)
    def populate(self, request, dbsession):
        import os
        import transaction
        from occams import models
        from occams_datastore import models as datastore

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            dbsession.info['blame'] = user
            dbsession.add(user)
            export = models.Export(
                name='myexport',
                status='complete',
                owner_user=user)
            dbsession.add(export)
            dbsession.flush()
            self.url = self.url_fmt.format(export=export.id)
            with open('/tmp/myexport', 'w+') as fp:
                self.export_file_name = fp.name

        def rm():
            os.unlink(self.export_file_name)

        request.addfinalizer(rm)

    # "None" in this case indicates that the user is not a member of any group
    # But in this case it's the owner so it should still be allowed.
    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'consumer', None])
    def test_allowed(self, app, dbsession, group):
        environ = make_environ(groups=[group])
        app.get(self.url, extra_environ=environ, status=200)

    def test_not_owner(self, app, dbsession):
        import transaction
        from occams_datastore import models as datastore
        with transaction.manager:
            dbsession.add(datastore.User(key='somebody_else'))
        environ = make_environ(userid='somebody_else')
        app.get(self.url, extra_environ=environ, status=403)

    def test_not_authenticated(self, app, dbsession):
        app.get(self.url, status=401)
