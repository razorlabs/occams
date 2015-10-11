from tests import IntegrationFixture

class TestIncludeme(IntegrationFixture):

    def test_settings(self):
        """
        It should be able to sanitize export-specific settings
        """
        from tests import REDIS_URL
        input = {
            'celery.backend.url': REDIS_URL,
            'celery.broker.url': REDIS_URL,
            'studies.export.user': 'dummy',
            'studies.export.dir': '/tmp',
            'studies.export.limit': '1234',
            'studies.export.expire': '123'
        }

        expected = input.copy()
        expected['studies.export.limit'] = \
            int(expected['studies.export.limit'])
        expected['studies.export.expire'] = \
            int(expected['studies.export.expire'])

        self.config.registry.settings.update(input)
        self.config.include('occams_studies.tasks')
        for key in input.keys():
            self.assertEquals(
                self.config.registry.settings[key],
                expected[key])


class TestMakeExport:

    def setUp(self):
        super(TestMakeExport, self).setUp()
        import tempfile
        import mock
        from redis import StrictRedis

        from occams.celery import app, Session
        from occams_studies import models
        from tests import REDIS_URL

        tmpdir = tempfile.mkdtemp()
        self.config.registry.settings['studies.export.dir'] = tmpdir
        app.userid = 'dummy'
        self.config.registry.settings['studies.export.user'] = 'dummy'
        Session.add(models.User(key='dummy'))
        Session.flush()
        self.celery = app
        self.celery.redis = StrictRedis.from_url(REDIS_URL)
        self.celery.settings = self.config.registry.settings

        # Block tasks from commiting to prevent test sideeffects
        self.commitmock = mock.patch('occams_studies.tasks.Session.commit')
        self.commitmock.start()

    def tearDown(self):
        super(TestMakeExport, self).tearDown()
        import shutil
        import mock
        shutil.rmtree(self.celery.settings['studies.export.dir'])
        mock.patch.stopall()

    def test_zip(self):
        """
        It should generate a zip file containing the specified contents
        """
        from zipfile import ZipFile
        from occams.celery import Session
        from occams_studies import models, tasks

        owner = models.User(key=u'joe')
        Session.info['blame'] = owner
        Session.info['settings'] = self.config.registry.settings
        Session.add(owner)
        Session.flush()

        export = models.Export(
            owner_user=owner,
            contents=[{'name': 'pid', 'title': 'PID', 'versions': []}],
            status='complete')
        Session.add(export)
        Session.flush()

        tasks.make_export(export.name)

        # @in_transaction removes the session metadata, so we gotta do this
        Session.info['settings'] = self.config.registry.settings
        export = Session.merge(export)

        with ZipFile(export.path, 'r') as zfp:
            self.assertItemsEqual(['pid.csv', 'codebook.csv'], zfp.namelist())
