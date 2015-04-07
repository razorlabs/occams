from ddt import ddt, data

from tests import FunctionalFixture


@ddt
class TestPermissionsAbout(FunctionalFixture):

    url = '/studies/exports'

    @data('administrator', 'consumer')
    def test_allowed(self, group):
        environ = self.make_environ(groups=[group])
        self.app.get(self.url, extra_environ=environ, status=200)

    @data(None)
    def test_not_allowed(self, group):
        environ = self.make_environ(groups=[group])
        self.app.get(self.url, extra_environ=environ, status=403)

    def test_not_authenticated(self):
        self.app.get(self.url, status=404)


@ddt
class TestExportViewPermissionsFaq(FunctionalFixture):

    url = '/studies/exports/faq'

    @data('administrator', 'consumer')
    def test_allowed(self, group):
        environ = self.make_environ(groups=[group])
        self.app.get(self.url, extra_environ=environ, status=200)

    def test_not_allowed(self, group):
        environ = self.make_environ(groups=[group])
        self.app.get(self.url, extra_environ=environ, status=403)

    def test_not_authenticated(self):
        self.app.get(self.url, status=403)


@ddt
class TestPermissionsAdd(FunctionalFixture):

    url = '/studies/exports/add'

    @data('administrator', 'consumer')
    def test_allowed(self, group):
        environ = self.make_environ(groups=[group])
        self.app.get(self.url, extra_environ=environ, status=403)

    def test_not_allowed(self, group):
        environ = self.make_environ(groups=[])
        self.app.get(self.url, extra_environ=environ, status=403)

    def test_not_authenticated(self):
        self.app.get(self.url, status=403)


@ddt
class TestPermissionsStatus(FunctionalFixture):

    url = '/studies/exports/status'

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

    @data('administrator', 'consumer')
    def test_allowed(self, group):
        environ = self.make_environ(groups=[group])
        self.app.get(self.url, extra_environ=environ, status=200)

    @data(None)
    def test_not_allowed(self, group):
        environ = self.make_environ(groups=[])
        self.app.get(self.url, extra_environ=environ, status=403)

    def test_not_authenticated(self):
        self.app.get(self.url, status=403)


@ddt
class TestPersmissionsDownload(FunctionalFixture):

    url = '/studies/exports/123/download'

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
