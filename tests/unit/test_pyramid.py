try:
    import unittest2 as unittest
except ImportError:
    import unittest


def setup_module():
    try:
        import pyramid  # NOQA
    except ImportError:
        from nose.exc import SkipTest
        raise SkipTest('Pyramid is not installed')


class PyramidIntegrationTestCase(unittest.TestCase):
    """
    Verifies proper integration with Pyramid (if available)
    """

    def setUp(self):
        from pyramid import testing
        self.config = testing.setUp()

    def tearDown(self):
        from pyramid import testing
        from occams.roster import Session
        testing.tearDown()
        Session.remove()

    def test_includeme(self):
        """
        It should register the database
        """
        from tempfile import NamedTemporaryFile
        from occams.roster import Session
        with NamedTemporaryFile() as fp:
            url = 'sqlite:///' + fp.name
            self.config.registry.settings['pid.db.url'] = url
            self.config.include('occams.roster')
            self.assertEqual(url, str(Session.bind.url))
