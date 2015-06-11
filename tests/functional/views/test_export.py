from ddt import ddt, data

from tests import FunctionalFixture, USERID


@ddt
class TestPermissionsAbout(FunctionalFixture):

    url = '/studies/exports'

    def setUp(self):
        super(TestPermissionsAbout, self).setUp()

        import transaction
        from occams import Session
        from occams_datastore import models as datastore

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            Session.add(datastore.User(key=USERID))

    @data('administrator', 'consumer')
    def test_allowed(self, group):
        environ = self.make_environ(userid=USERID, groups=[group])
        self.app.get(self.url, extra_environ=environ, status=200)

    @data(None)
    def test_not_allowed(self, group):
        environ = self.make_environ(userid=USERID, groups=[group])
        self.app.get(self.url, extra_environ=environ, status=403)

    def test_not_authenticated(self):
        self.app.get(self.url, status=401)


@ddt
class TestExportViewPermissionsFaq(FunctionalFixture):

    url = '/studies/exports/faq'

    def setUp(self):
        super(TestExportViewPermissionsFaq, self).setUp()

        import transaction
        from occams import Session
        from occams_datastore import models as datastore

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            Session.add(datastore.User(key=USERID))

    @data('administrator', 'manager', 'consumer')
    def test_allowed(self, group):
        environ = self.make_environ(userid=USERID, groups=[group])
        self.app.get(self.url, extra_environ=environ, status=200)

    @data(None)
    def test_not_allowed(self, group):
        environ = self.make_environ(userid=USERID, groups=[group])
        self.app.get(self.url, extra_environ=environ, status=403)

    def test_not_authenticated(self):
        self.app.get(self.url, status=401)


@ddt
class TestPermissionsCheckout(FunctionalFixture):

    url = '/studies/exports/checkout'

    def setUp(self):
        super(TestPermissionsCheckout, self).setUp()

        import transaction
        from occams import Session
        from occams_datastore import models as datastore

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            Session.add(datastore.User(key=USERID))

    @data('administrator', 'manager', 'consumer')
    def test_allowed(self, group):
        environ = self.make_environ(userid=USERID, groups=[group])
        self.app.get(self.url, extra_environ=environ, status=200)

    @data(None)
    def test_not_allowed(self, group):
        environ = self.make_environ(userid=USERID, groups=[group])
        self.app.get(self.url, extra_environ=environ, status=403)

    def test_not_authenticated(self):
        self.app.get(self.url, status=401)


@ddt
class TestPermissionsStatus(FunctionalFixture):

    url = '/studies/exports/status'

    def setUp(self):
        super(TestPermissionsStatus, self).setUp()

        import transaction
        from occams import Session
        from occams_datastore import models as datastore

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            Session.add(datastore.User(key=USERID))

    @data('administrator', 'manager', 'consumer')
    def test_allowed(self, group):
        environ = self.make_environ(groups=[group])
        self.app.get(self.url, extra_environ=environ, status=200)

    @data(None)
    def test_not_allowed(self, group):
        environ = self.make_environ(groups=[group])
        self.app.get(self.url, extra_environ=environ, status=403)

    def test_not_authenticated(self):
        self.app.get(self.url, status=401)


@ddt
class TestPermissionsStatusJSON(FunctionalFixture):

    url = '/studies/exports/status'

    def setUp(self):
        super(TestPermissionsStatusJSON, self).setUp()

        import transaction
        from occams import Session
        from occams_datastore import models as datastore

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            Session.add(datastore.User(key=USERID))

    @data('administrator', 'manager', 'consumer')
    def test_allowed(self, group):
        environ = self.make_environ(groups=[group])
        self.app.get(self.url, extra_environ=environ, xhr=True, status=200)

    @data(None)
    def test_not_allowed(self, group):
        environ = self.make_environ(groups=[group])
        self.app.get(self.url, extra_environ=environ, xhr=True, status=403)

    def test_not_authenticated(self):
        self.app.get(self.url, xhr=True, status=401)


@ddt
class TestPersmissionsDelete(FunctionalFixture):

    url_fmt = '/studies/exports/{export}'

    def setUp(self):
        super(TestPersmissionsDelete, self).setUp()

        import transaction
        from occams import Session
        from occams_datastore import models as datastore
        from occams_studies import models

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            Session.info['blame'] = user
            Session.add(user)
            export = models.Export(owner_user=user)
            Session.add(export)
            Session.flush()
            self.url = self.url_fmt.format(export=export.id)

    # None indicates current user
    @data('administrator', 'manager', 'consumer', None)
    def test_allowed(self, group):
        environ = self.make_environ(groups=[group])
        csrf_token = self.get_csrf_token(environ)
        self.app.delete(
            self.url,
            extra_environ=environ,
            headers={'X-CSRF-Token': csrf_token},
            xhr=True,
            status=200)

    def test_not_owner(self):
        import transaction
        from occams_studies import Session, models
        with transaction.manager:
            Session.add(models.User(key='somebody_else'))
        environ = self.make_environ(userid='somebody_else')
        csrf_token = self.get_csrf_token(environ)
        self.app.delete(
            self.url,
            extra_environ=environ,
            headers={'X-CSRF-Token': csrf_token},
            xhr=True,
            status=403)

    def test_not_authenticated(self):
        self.app.delete(self.url, xhr=True, status=401)


@ddt
class TestPersmissionsCodebook(FunctionalFixture):

    url = '/studies/exports/codebook'

    def setUp(self):
        super(TestPersmissionsCodebook, self).setUp()

        import transaction
        from occams import Session
        from occams_datastore import models as datastore

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            Session.add(datastore.User(key=USERID))

    @data('administrator', 'manager', 'consumer')
    def test_allowed(self, group):
        environ = self.make_environ(groups=[group])
        self.app.get(self.url, extra_environ=environ, status=200)

    @data(None)
    def test_not_allowed(self, group):
        environ = self.make_environ(groups=[group])
        self.app.get(self.url, extra_environ=environ, status=403)

    def test_not_authenticated(self):
        self.app.get(self.url, status=401)


@ddt
class TestPersmissionsCodebookJSON(FunctionalFixture):

    url = '/studies/exports/codebook'

    def setUp(self):
        super(TestPersmissionsCodebookJSON, self).setUp()

        import transaction
        from occams import Session
        from occams_datastore import models as datastore

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            Session.add(datastore.User(key=USERID))

    @data('administrator', 'manager', 'consumer')
    def test_allowed(self, group):
        environ = self.make_environ(groups=[group])
        self.app.get(
            self.url,
            {'file': 'pid'},
            extra_environ=environ,
            xhr=True,
            status=200)

    @data(None)
    def test_not_allowed(self, group):
        environ = self.make_environ(groups=[group])
        self.app.get(
            self.url,
            {'file': 'pid'},
            extra_environ=environ,
            xhr=True,
            status=403)

    def test_not_authenticated(self):
        self.app.get(self.url, status=401)


@ddt
class TestPersmissionsCodebookDownload(FunctionalFixture):

    url = '/studies/exports/codebook?alt=csv'

    def setUp(self):
        super(TestPersmissionsCodebookDownload, self).setUp()

        import transaction
        from occams import Session
        from occams_datastore import models as datastore

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            Session.add(datastore.User(key=USERID))

        # XXX: need to somehow get the settings so we can consitently
        #      get the correct directory
        with open('/tmp/codebook.csv', 'w+') as fp:
            self.codebook_file_name = fp.name

    def tearDown(self):
        import os
        os.unlink(self.codebook_file_name)
        super(TestPersmissionsCodebookDownload, self).tearDown()

    @data('administrator', 'manager', 'consumer')
    def test_allowed(self, group):
        environ = self.make_environ(groups=[group])
        self.app.get(self.url, extra_environ=environ, status=200)

    @data(None)
    def test_not_allowed(self, group):
        environ = self.make_environ(groups=[group])
        self.app.get(self.url, extra_environ=environ, status=403)

    def test_not_authenticated(self):
        self.app.get(self.url, status=401)


@ddt
class TestPermissionsDownload(FunctionalFixture):

    url_fmt = '/studies/exports/{export}/download'

    def setUp(self):
        super(TestPermissionsDownload, self).setUp()

        import transaction
        from occams_studies import Session, models
        from occams_datastore import models as datastore

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            Session.info['blame'] = user
            Session.add(user)
            export = models.Export(
                name='myexport',
                status='complete',
                owner_user=user)
            Session.add(export)
            Session.flush()
            self.url = self.url_fmt.format(export=export.id)
            with open('/tmp/myexport', 'w+') as fp:
                self.export_file_name = fp.name

    def tearDown(self):
        import os
        os.unlink(self.export_file_name)
        super(TestPermissionsDownload, self).tearDown()

    # "None" in this case indicates that the user is not a member of any group
    # But in this case it's the owner so it should still be allowed.
    @data('administrator', 'manager', 'consumer', None)
    def test_allowed(self, group):
        environ = self.make_environ(groups=[group])
        self.app.get(self.url, extra_environ=environ, status=200)

    def test_not_owner(self):
        import transaction
        from occams_studies import Session, models
        with transaction.manager:
            Session.add(models.User(key='somebody_else'))
        environ = self.make_environ(userid='somebody_else')
        self.app.get(self.url, extra_environ=environ, status=403)

    def test_not_authenticated(self):
        self.app.get(self.url, status=401)
