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
        self.app.get(self.url, status=404)


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

    @data('administrator', 'consumer')
    def test_allowed(self, group):
        environ = self.make_environ(userid=USERID, groups=[group])
        self.app.get(self.url, extra_environ=environ, status=200)

    def test_not_allowed(self, group):
        environ = self.make_environ(userid=USERID, groups=[group])
        self.app.get(self.url, extra_environ=environ, status=403)

    def test_not_authenticated(self):
        self.app.get(self.url, status=403)


@ddt
class TestPermissionsAdd(FunctionalFixture):

    url = '/studies/exports/add'

    def setUp(self):
        super(TestPermissionsAdd, self).setUp()

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
        self.app.get(self.url, extra_environ=environ, status=403)

    def test_not_allowed(self, group):
        environ = self.make_environ(userid=USERID, groups=[group])
        self.app.get(self.url, extra_environ=environ, status=403)

    def test_not_authenticated(self):
        self.app.get(self.url, status=403)


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

    @data('administrator', 'consumer')
    def test_allowed(self, group):
        environ = self.make_environ(groups=[group])
        self.app.get(self.url, extra_environ=environ, status=200)

    @data(None)
    def test_not_allowed(self, group):
        environ = self.make_environ(groups=[group])
        self.app.get(self.url, extra_environ=environ, status=403)

    def test_not_authenticated(self):
        self.app.get(self.url, status=403)


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

    @data('administrator', 'consumer')
    def test_allowed(self, group):
        environ = self.make_environ(groups=[group])
        self.app.get(self.url, extra_environ=environ, xhr=True, status=200)

    @data(None)
    def test_not_allowed(self, group):
        environ = self.make_environ(groups=[group])
        self.app.get(self.url, extra_environ=environ, xhr=True, status=403)

    def test_not_authenticated(self):
        self.app.get(self.url, xhr=True, status=200)


@ddt
class TestPersmissionsDelete(FunctionalFixture):

    url = '/studies/exports/123/delete'

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
            Session.add(user)
            Session.add(models.Export(id=123, owner_user=user))

    @data('administrator', 'consumer')
    def test_allowed(self, group):
        environ = self.make_environ(groups=[group])
        self.app.post(self.url, extra_environ=environ, xhr=True, status=200)

    @data(None)
    def test_not_allowed(self, group):
        environ = self.make_environ(groups=[group])
        self.app.post(self.url, extra_environ=environ, xhr=True, status=403)

    def test_not_authenticated(self):
        self.app.post(self.url, xhr=True, status=403)


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

    @data('administrator', 'consumer')
    def test_allowed(self, group):
        environ = self.make_environ(groups=[group])
        self.app.get(self.url, extra_environ=environ, status=200)

    @data(None)
    def test_not_allowed(self, group):
        environ = self.make_environ(groups=[group])
        self.app.get(self.url, extra_environ=environ, status=200)

    def test_not_authenticated(self):
        self.app.get(self.url, status=403)


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

    @data('administrator', 'consumer')
    def test_allowed(self, group):
        environ = self.make_environ(groups=[group])
        self.app.get(self.url, extra_environ=environ, xhr=True, status=403)

    @data(None)
    def test_not_allowed(self, group):
        environ = self.make_environ(groups=[group])
        self.app.get(self.url, extra_environ=environ, xhr=True, status=403)

    def test_not_authenticated(self):
        self.app.get(self.url, status=403)


@ddt
class TestPersmissionsCodebookDownload(FunctionalFixture):

    url = '/studies/exports/codebook/download'

    def setUp(self):
        super(TestPersmissionsCodebookDownload, self).setUp()

        import transaction
        from occams import Session
        from occams_datastore import models as datastore

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            Session.add(datastore.User(key=USERID))

    @data('administrator', 'consumer')
    def test_allowed(self, group):
        environ = self.make_environ(groups=[group])
        self.app.get(self.url, extra_environ=environ, status=200)

    @data(None)
    def test_not_allowed(self, group):
        environ = self.make_environ(groups=[group])
        self.app.get(self.url, extra_environ=environ, status=403)

    def test_not_authenticated(self):
        self.app.get(self.url, status=403)


@ddt
class TestPersmissionsDownload(FunctionalFixture):

    url = '/studies/exports/123/download'

    def setUp(self):
        super(TestPersmissionsDownload, self).setUp()

        import transaction
        from occams import Session
        from occams_datastore import models as datastore

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            Session.add(datastore.User(key=USERID))

    @data('administrator', 'consumer')
    def test_allowed(self, group):
        environ = self.make_environ(groups=[group])
        self.app.get(self.url, extra_environ=environ, status=200)

    @data(None)
    def test_not_allowed(self, group):
        environ = self.make_environ(groups=[group])
        self.app.get(self.url, extra_environ=environ, status=403)

    def test_not_authenticated(self):
        self.app.get(self.url, status=403)
