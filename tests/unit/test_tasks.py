import unittest

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
        input = {
            'app.export.user': 'dummy',
            'app.export.dir': '/tmp',
            'celery.broker.url': 'redis:///9',
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


class TestInTransaction(unittest.TestCase):
    """
    Functional-ish test that ensures tasks can be completed in a transaction.
    """

    def test_remove(self):
        """
        It should disconnect the database after each task.
        """
        import celery
        from sqlalchemy import Column, Integer, orm
        from sqlalchemy.ext.declarative import declarative_base
        from occams.studies import Session
        from occams.studies.tasks import in_transaction

        app = celery.Celery('test')

        Model = declarative_base()

        class Dummy(Model):
            __tablename__ = 'dummy'
            id = Column(Integer, primary_key=True)

        Model.metadata.create_all(Session.bind)

        @app.task()
        @in_transaction
        def do_something():
            ret = Dummy()
            Session.add(ret)
            return ret

        self.assertEquals(Session.query(Dummy).count(), 0)

        ret = do_something()

        # The transaction/connection should no longer be available
        with self.assertRaises(orm.exc.DetachedInstanceError):
            # Accessing an attribute from another connection angers sqlalchemy
            ret.id

        self.assertEquals(Session.query(Dummy).count(), 1)

        Model.metadata.drop_all(Session.bind)


class TestInit(IntegrationFixture):

    def test_init(self):
        """
        It should use the pyramid application to initalize settings/resources
        """
        import mock
        from occams.studies import Session, models
        from occams.studies.tasks import init

        with mock.patch('occams.studies.tasks.bootstrap') as bootstrap:
            bootstrap.return_value = {
                'registry': mock.Mock(
                    settings={
                        'app.export.user': 'celery_user',
                    }),
                'request': mock.Mock(redis=mock.Mock())}

            signal = mock.Mock()
            sender = mock.Mock(options={'ini': 'app.ini'})

            init(signal, sender)

            # App should now be configured with pyramid's settings
            self.assertIn('app.export.user', sender.app.settings)
            self.assertIsNotNone(sender.app.redis)
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
        from occams.studies.security import track_user

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
