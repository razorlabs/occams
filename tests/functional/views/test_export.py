from ddt import ddt, data

from tests import FunctionalFixture


@ddt
class TestListViewPermissions(FunctionalFixture):

    url = '/data'

    @data('administrator', 'investigator', 'statistician', 'researcher',
          'nurse')
    def test_allowed(self, principal):
        """
        It should allow administrative personnel to view form listings
        """
        self.assert_can_view(self.url, self.make_environ(groups=[principal]))

    @data('assistant', 'student', None)
    def test_not_allowed(self, principal):
        """
        It should not allow data entry prinicipals to view form listings
        """
        self.assert_cannot_view(self.url, self.make_environ(groups=[principal]))

    def test_unauthenticated_not_allowed(self):
        """
        It should not allow unauthenticated users to view form listings
        """
        self.assert_cannot_view(self.url)


@ddt
class TestExportViewPermissions(FunctionalFixture):

    url = '/data/exports'

    @data('administrator', 'investigator', 'statistician', 'researcher',
          'nurse')
    def test_allowed(self, principal):
        """
        It should allow administrative personnel to view downloads
        """
        self.assert_can_view(self.url, self.make_environ(groups=[principal]))

    @data('assistant', 'student', None)
    def test_not_allowed(self, principal):
        """
        It should not allow data entry prinicipals to view downloads
        """
        self.assert_cannot_view(self.url, self.make_environ(groups=[principal]))

    def test_unauthenticated_not_allowed(self):
        """
        It should not allow unauthenticated users to view downloads
        """
        self.assert_cannot_view(self.url)


@ddt
class TestDownloadViewPersmissions(FunctionalFixture):

    url = '/data/exports/123'

    @data('administrator', 'investigator', 'statistician', 'researcher',
          'nurse')
    def test_allowed(self, principal):
        """
        It should allow administrative personnel to download exports
        """
        import transaction
        from occams.clinical import Session, models
        environ = self.make_environ(groups=[principal])
        # Add the the export zip file and database record
        with open('/tmp/123.zip', 'wb+'):
            with transaction.manager:
                self.add_user(environ['REMOTE_USER'])
                Session.add(models.Export(
                    id=123,
                    owner_user=(
                        Session.query(models.User)
                        .filter_by(key=environ['REMOTE_USER'])
                        .one()),
                    status='complete'))
            self.assert_can_view(self.url, environ)

    @data('assistant', 'student', None)
    def test_not_allowed(self, principal):
        """
        It should not allow data entry prinicipals to download exports
        """
        self.assert_cannot_view(self.url, self.make_environ(groups=[principal]))

    def test_unauthenticated_not_allowed(self):
        """
        It should not allow unauthenticated users to download exports
        """
        self.assert_cannot_view(self.url)
