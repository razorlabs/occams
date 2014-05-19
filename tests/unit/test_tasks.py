from tests import IntegrationFixture


class TestIncludeme(IntegrationFixture):

    def setUp(self):
        super(TestIncludeme, self).setUp()
        import mock

        self.patch = mock.patch('occams.studies.tasks.celery.conf')
        self.patch.start()

    def tearDown(self):
        super(TestIncludeme, self).tearDown()
        import mock
        mock.patch.stopall()

    def test_settings(self):
        """
        It should be able to sanitize export-specific settings
        """
        from tests import REDIS_URL
        input = {
            'app.export.user': 'dummy',
            'app.export.dir': '/tmp',
            'celery.broker.url': REDIS_URL,
            'celery.backend.url': REDIS_URL,
            'app.export.limit': '1234',
            'app.export.expire': '123'
        }

        expected = input.copy()
        expected['app.export.limit'] = int(expected['app.export.limit'])
        expected['app.export.expire'] = int(expected['app.export.expire'])

        self.config.registry.settings.update(input)
        self.config.include('occams.studies.tasks')
        for key in input.keys():
            self.assertEquals(
                self.config.registry.settings[key],
                expected[key])


class TestInit(IntegrationFixture):

    def test_init(self):
        """
        It should use the pyramid application to initalize settings/resources
        """
        import mock
        from occams.studies import Session, models
        from occams.studies.tasks import on_preload_parsed

        with mock.patch('occams.studies.tasks.bootstrap') as bootstrap:
            bootstrap.return_value = {
                'registry': mock.Mock(
                    settings={
                        'app.export.user': 'celery_user',
                    }),
                'request': mock.Mock(redis=mock.Mock())}

            with mock.patch('occams.studies.tasks.celery') as celery:
                on_preload_parsed({'ini': 'app.ini'})

                # App should now be configured with pyramid's settings
                self.assertIn('app.export.user', celery.settings)
                self.assertIsNotNone(celery.redis)
                self.assertIsNotNone(
                    Session.query(models.User)
                    .filter_by(key='celery_user')
                    .first())


class TestMakeExport(IntegrationFixture):

    def setUp(self):
        super(TestMakeExport, self).setUp()
        import tempfile
        import mock
        from redis import StrictRedis
        from occams.studies.tasks import celery
        from tests import REDIS_URL

        self.config.registry.settings['app.export.dir'] = tempfile.mkdtemp()
        self.celery = celery
        self.celery.redis = StrictRedis.from_url(REDIS_URL)
        self.celery.settings = self.config.registry.settings

        # Block tasks from commiting to prevent test sideeffects
        self.transaction = mock.patch('occams.studies.tasks.transaction')
        self.transaction.start()

    def tearDown(self):
        super(TestMakeExport, self).tearDown()
        import shutil
        import mock
        shutil.rmtree(self.celery.settings['app.export.dir'])
        mock.patch.stopall()

    def test_zip(self):
        """
        It should generate a zip file containing the specified contents
        """
        from zipfile import ZipFile
        from occams.studies import Session, models
        from occams.studies.tasks import make_export
        from tests import track_user

        track_user('joe')
        export = models.Export(
            owner_user=(
                Session.query(models.User).filter_by(key='joe').one()),
            contents=[{'name': 'pid', 'title': 'PID', 'versions': []}],
            status='complete')
        Session.add(export)
        Session.flush()

        make_export(export.name)

        with ZipFile(export.path, 'r') as zfp:
            self.assertItemsEqual(['pid.csv', 'codebook.csv'], zfp.namelist())
