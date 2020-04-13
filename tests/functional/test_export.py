import pytest
from tests.testing import USERID, make_environ, get_csrf_token


class TestPermissionsAbout:

    url = '/studies/exports'

    @pytest.mark.parametrize('group', ['administrator', 'consumer'])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        testapp.get(self.url, extra_environ=environ, status=200)

    @pytest.mark.parametrize('group', [None])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        testapp.get(self.url, extra_environ=environ, status=403)

    def test_not_authenticated(self, testapp):
        testapp.get(self.url, status=401)


class TestExportViewPermissionsFaq:

    url = '/studies/exports/faq'

    @pytest.mark.parametrize('group', ['administrator', 'manager', 'consumer'])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        testapp.get(self.url, extra_environ=environ, status=200)

    @pytest.mark.parametrize('group', [None])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        testapp.get(self.url, extra_environ=environ, status=403)

    def test_not_authenticated(self, testapp):
        testapp.get(self.url, status=401)


class TestPermissionsCheckout:

    url = '/studies/exports/checkout'

    @pytest.mark.parametrize('group', ['administrator', 'manager', 'consumer'])
    def test_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        testapp.get(self.url, extra_environ=environ, status=200)

    @pytest.mark.parametrize('group', [None])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(userid=USERID, groups=[group])
        testapp.get(self.url, extra_environ=environ, status=403)

    def test_not_authenticated(self, testapp):
        testapp.get(self.url, status=401)


class TestPermissionsStatus:

    url = '/studies/exports/status'

    @pytest.mark.parametrize('group', ['administrator', 'manager', 'consumer'])
    def test_allowed(self, testapp, group):
        environ = make_environ(groups=[group])
        testapp.get(self.url, extra_environ=environ, status=200)

    @pytest.mark.parametrize('group', [None])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(groups=[group])
        testapp.get(self.url, extra_environ=environ, status=403)

    def test_not_authenticated(self, testapp):
        testapp.get(self.url, status=401)


class TestPermissionsStatusJSON:

    url = '/studies/exports/status'

    @pytest.mark.parametrize('group', ['administrator', 'manager', 'consumer'])
    def test_allowed(self, testapp, group):
        environ = make_environ(groups=[group])
        testapp.get(self.url, extra_environ=environ, xhr=True, status=200)

    @pytest.mark.parametrize('group', [None])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(groups=[group])
        testapp.get(self.url, extra_environ=environ, xhr=True, status=403)

    def test_not_authenticated(self, testapp):
        testapp.get(self.url, xhr=True, status=401)


class TestPermissionsNotifications:

    url = '/studies/exports/notifications'

    @pytest.mark.parametrize('group', ['administrator', 'manager', 'consumer'])
    def test_allowed(self, testapp, group):
        environ = make_environ(groups=[group])
        testapp.get(self.url, extra_environ=environ, xhr=True, status=200)

    @pytest.mark.parametrize('group', [None])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(groups=[group])
        testapp.get(self.url, extra_environ=environ, xhr=True, status=403)

    def test_not_authenticated(self, testapp):
        testapp.get(self.url, xhr=True, status=401)


class TestPersmissionsDelete:

    url_fmt = '/studies/exports/{export}'

    @pytest.fixture(autouse=True)
    def populate(self, request, app, using_dbsession):
        from occams import models
        from datetime import date

        with using_dbsession(app) as dbsession:
            user = dbsession.query(models.User).filter_by(key=USERID).one()
            export = models.Export(owner_user=user, contents=[])
            dbsession.add(models.User(key='somebody_else'))
            dbsession.add(export)
            dbsession.flush()
            self.url = self.url_fmt.format(export=export.id)

        def cleanup():
            with using_dbsession(app) as dbsession:
                dbsession.delete(
                    dbsession.query(models.User)
                    .filter_by(key='somebody_else')
                    .one()
                )

        request.addfinalizer(cleanup)

    # None indicates current user
    @pytest.mark.parametrize('group', [
        'administrator', 'manager', 'consumer', None])
    def test_allowed(self, testapp, group):
        environ = make_environ(groups=[group])
        csrf_token = get_csrf_token(testapp, environ)
        testapp.delete(
            self.url,
            extra_environ=environ,
            headers={'X-CSRF-Token': csrf_token},
            xhr=True,
            status=200)

    def test_not_owner(self, testapp):
        environ = make_environ(userid='somebody_else')
        csrf_token = get_csrf_token(testapp, environ)
        testapp.delete(
            self.url,
            extra_environ=environ,
            headers={'X-CSRF-Token': csrf_token},
            xhr=True,
            status=403)

    def test_not_authenticated(self, testapp):
        testapp.delete(self.url, xhr=True, status=401)


class TestPersmissionsCodebook:

    url = '/studies/exports/codebook'

    @pytest.mark.parametrize('group', ['administrator', 'manager', 'consumer'])
    def test_allowed(self, testapp, group):
        environ = make_environ(groups=[group])
        testapp.get(self.url, extra_environ=environ, status=200)

    @pytest.mark.parametrize('group', [None])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(groups=[group])
        testapp.get(self.url, extra_environ=environ, status=403)

    def test_not_authenticated(self, testapp):
        testapp.get(self.url, status=401)


class TestPersmissionsCodebookJSON:

    url = '/studies/exports/codebook'

    @pytest.mark.parametrize('group', ['administrator', 'manager', 'consumer'])
    def test_allowed(self, testapp, group):
        environ = make_environ(groups=[group])
        testapp.get(
            self.url,
            {'file': 'pid'},
            extra_environ=environ,
            xhr=True,
            status=200)

    @pytest.mark.parametrize('group', [None])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(groups=[group])
        testapp.get(
            self.url,
            {'file': 'pid'},
            extra_environ=environ,
            xhr=True,
            status=403)

    def test_not_authenticated(self, testapp):
        testapp.get(self.url, status=401)


class TestPersmissionsCodebookDownload:

    url = '/studies/exports/codebook?alt=csv'

    @pytest.fixture(autouse=True)
    def populate(self, request):
        import os

        # XXX: need to somehow get the settings so we can consitently
        #      get the correct directory
        with open('/tmp/codebook.csv', 'w+') as fp:
            self.codebook_file_name = fp.name

        def rm():
            os.unlink(self.codebook_file_name)

        request.addfinalizer(rm)

    @pytest.mark.parametrize('group', ['administrator', 'manager', 'consumer'])
    def test_allowed(self, testapp, group):
        environ = make_environ(groups=[group])
        testapp.get(self.url, extra_environ=environ, status=200)

    @pytest.mark.parametrize('group', [None])
    def test_not_allowed(self, testapp, group):
        environ = make_environ(groups=[group])
        testapp.get(self.url, extra_environ=environ, status=403)

    def test_not_authenticated(self, testapp):
        testapp.get(self.url, status=401)


class TestPermissionsDownload:

    url_fmt = '/studies/exports/{export}/download'

    @pytest.fixture(autouse=True)
    def populate(self, request, app, using_dbsession):
        import os
        from occams import models
        from datetime import date

        with using_dbsession(app) as dbsession:
            export = models.Export(
                name='myexport',
                status='complete',
                owner_user=dbsession.query(models.User).filter_by(key=USERID).one(),
                contents=[],
            )
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
    def test_allowed(self, testapp, group):
        environ = make_environ(groups=[group])
        testapp.get(self.url, extra_environ=environ, status=200)

    def test_not_owner(self, testapp):
        environ = make_environ(userid='somebody_else')
        testapp.get(self.url, extra_environ=environ, status=403)

    def test_not_authenticated(self, testapp):
        testapp.get(self.url, status=401)
