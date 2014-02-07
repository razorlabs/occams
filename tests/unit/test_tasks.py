# -*- coding: utf-8 -*-
import unittest
from tests import PubSubListener, IntegrationFixture, REDIS_URL, CLINICAL_URL


class TestInTransaction(unittest.TestCase):
    """
    Functional-ish test that ensures tasks can be completed in a transaction.
    """

    def setUp(self):
        from sqlalchemy import create_engine
        from occams.clinical import Session
        Session.configure(bind=create_engine(CLINICAL_URL))

    def tearDown(self):
        from occams.clinical import Session
        Session.remove()

    def test_remove(self):
        """
        It should disconnect the database after each task.
        """
        import celery
        from sqlalchemy import Column, Integer, orm
        from sqlalchemy.ext.declarative import declarative_base
        from occams.clinical import Session
        from occams.clinical.tasks import in_transaction

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


class TestInit(IntegrationFixture):

    def test_init(self):
        """
        It should use the pyramid application to initalize settings/resources
        """
        import mock
        from redis import StrictRedis
        from occams.clinical.tasks import init

        with mock.patch('occams.clinical.tasks.bootstrap') as bootstrap:
            bootstrap.return_value = {
                'registry': mock.Mock(settings={'misc_setting': True}),
                'request': mock.Mock(redis=StrictRedis.from_url(REDIS_URL))}

            signal = mock.Mock()
            sender = mock.Mock(options={'ini': 'whocares.ini'})

            init(signal, sender)

            # App should now be configured with pyramid's settings
            self.assertIn('misc_setting', sender.app.settings)
            self.assertIsInstance(sender.app.redis, StrictRedis)


class TestMakeExport(IntegrationFixture):

    def setUp(self):
        super(TestMakeExport, self).setUp()
        import tempfile
        import mock
        from redis import StrictRedis
        from occams.clinical.tasks import app
        self.app = app
        self.app.redis = StrictRedis.from_url(REDIS_URL)
        self.app.settings = {'app.export_dir': tempfile.mkdtemp()}

        # Need a listener on another thread for publish notifications
        self.client = PubSubListener(StrictRedis.from_url(REDIS_URL), 'export')
        self.client.start()

        # Block tasks from commiting to prevent test sideeffects
        self.patch = mock.patch('occams.clinical.tasks.transaction')
        self.patch.start()

    def tearDown(self):
        super(TestMakeExport, self).tearDown()
        import shutil
        self.app.redis.publish('export', 'KILL')
        shutil.rmtree(self.app.settings['app.export_dir'])
        self.patch.stop()

    def test_empty(self):
        """
        It should fail if there is no schemata in the export job
        """
        from occams.clinical import Session, models
        from occams.clinical.tasks import make_export

        self.add_user('joe')
        export = models.Export(
            owner_user=(
                Session.query(models.User).filter_by(key='joe').one()),
            status='pending')
        Session.add(export)
        Session.flush()

        with self.assertRaises(AssertionError):
            make_export(export.id)

    def test_fail_if_complete(self):
        """
        It should fail if it's already complete
        """
        from datetime import date
        from occams.clinical import Session, models
        from occams.clinical.tasks import make_export

        self.add_user('joe')
        export = models.Export(
            owner_user=(
                Session.query(models.User).filter_by(key='joe').one()),
            schemata=[
                models.Schema(
                    name=u'vitals',
                    title=u'Vitals',
                    publish_date=date.today())],
            status='complete')
        Session.add(export)
        Session.flush()

        with self.assertRaises(AssertionError):
            make_export(export.id)

    def test_one_schema_one_version(self):
        """
        It should generate one export and one codebook if the schema
        only has one version
        """
        from contextlib import closing
        from datetime import date
        import zipfile
        import os
        from occams.clinical import Session, models
        from occams.clinical.tasks import make_export

        today = date.today()
        redis = self.app.redis

        self.add_user('joe')
        export = models.Export(
            owner_user=(
                Session.query(models.User).filter_by(key='joe').one()),
            schemata=[
                models.Schema(
                    name=u'vitals',
                    title=u'Vitals',
                    publish_date=today)],
            status='pending')
        Session.add(export)
        Session.flush()

        make_export(export.id)
        export_file = os.path.join(
            self.app.settings['app.export_dir'], '%s.zip' % export.id)

        with closing(zipfile.ZipFile(export_file)) as zfp:
            self.assertItemsEqual(
                zfp.namelist(),
                ['vitals-codebook.csv', 'vitals-%s.csv' % today])

        self.assertDictEqual(
            redis.hgetall(export.id),
            {'export_id': str(export.id),
             'owner_user': 'joe',
             'status': 'complete',
             'count': '2',
             'total': '2'})

        # Record 1, Record 2, Complete messages
        self.assertEqual(len(self.client.messages), 3)

    def test_one_schema_multi_version(self):
        """
        It should generate one codebook for all versions of a schema
        """
        from contextlib import closing
        from datetime import date, timedelta
        import zipfile
        import os
        from occams.clinical import Session, models
        from occams.clinical.tasks import make_export

        t0 = date.today()
        t1 = t0 + timedelta(1)

        redis = self.app.redis

        self.add_user('joe')
        export = models.Export(
            owner_user=(
                Session.query(models.User).filter_by(key='joe').one()),
            schemata=[
                models.Schema(
                    name=u'vitals',
                    title=u'Vitals',
                    publish_date=t0),
                models.Schema(
                    name=u'vitals',
                    title=u'Vitals',
                    publish_date=t1)],
            status='pending')
        Session.add(export)
        Session.flush()

        make_export(export.id)
        export_file = os.path.join(
            self.app.settings['app.export_dir'], '%s.zip' % export.id)

        with closing(zipfile.ZipFile(export_file)) as zfp:
            self.assertItemsEqual(
                zfp.namelist(),
                ['vitals-codebook.csv',
                 'vitals-%s.csv' % t1,
                 'vitals-%s.csv' % t0])

        self.assertDictEqual(
            redis.hgetall(export.id),
            {'export_id': str(export.id),
             'owner_user': 'joe',
             'status': 'complete',
             'count': '3',
             'total': '3'})

        self.assertEqual(len(self.client.messages), 4)


class TestQueryReport(IntegrationFixture):

    def test_patient(self):
        """
        It should add patient-specific metdata to the report
        """
        from datetime import date
        from occams.clinical import Session, models
        from occams.clinical.tasks import query_report

        self.add_user(u'joe')
        entity = models.Entity(
            name=u'sample',
            title=u'',
            collect_date=date.today(),
            schema=models.Schema(
                name=u'vitals',
                title=u'Vitals',
                publish_date=date.today()))
        visit = models.Visit(
            patient=models.Patient(
                site=models.Site(name='ucsd', title=u'UCSD'),
                our=u'12345',
                entities=[entity]),
            visit_date=date.today(),
            entities=[entity])
        Session.add(visit)

        schema = Session.query(models.Schema).one()
        report = query_report(schema.name, [schema.id])
        entry = report.one()
        self.assertEquals(entry.site, 'ucsd')
        self.assertEquals(entry.pid, '12345')
        self.assertIsNone(entry.enrollment)
        self.assertIsNone(entry.cycles, None)
        self.assertEquals(entry.collect_date, date.today())

    def test_enrollment(self):
        """
        It should add enrollment-specific metdata to the report
        """
        from datetime import date, timedelta
        from occams.clinical import Session, models
        from occams.clinical.tasks import query_report

        self.add_user(u'joe')
        entity = models.Entity(
            name=u'sample',
            title=u'',
            collect_date=date.today(),
            schema=models.Schema(
                name=u'vitals',
                title=u'Vitals',
                publish_date=date.today()))
        enrollment = models.Enrollment(
            patient=models.Patient(
                site=models.Site(name='ucsd', title=u'UCSD'),
                our=u'12345',
                entities=[entity]),
            study=models.Study(
                name=u'cooties',
                short_title=u'CTY',
                code=u'999',
                consent_date=date.today() - timedelta(365),
                title=u'Cooties'),
            consent_date=date.today() - timedelta(5),
            latest_consent_date=date.today() - timedelta(3),
            termination_date=date.today(),
            entities=[entity])
        Session.add(enrollment)

        schema = Session.query(models.Schema).one()
        report = query_report(schema)
        entry = report.one()
        self.assertEquals(entry.site, 'ucsd')
        self.assertEquals(entry.pid, '12345')
        self.assertEquals(entry.enrollment, 'cooties')
        self.assertIsNone(entry.cycles, None)
        self.assertEquals(entry.collect_date, date.today())

    def test_visit(self):
        """
        It should add visit-specific metdata to the report
        """
        from datetime import date, timedelta
        from occams.clinical import Session, models
        from occams.clinical.tasks import query_report

        self.add_user(u'joe')
        entity = models.Entity(
            name=u'sample',
            title=u'',
            collect_date=date.today(),
            schema=models.Schema(
                name=u'vitals',
                title=u'Vitals',
                publish_date=date.today()))
        visit = models.Visit(
            visit_date=date.today(),
            patient=models.Patient(
                site=models.Site(name='ucsd', title=u'UCSD'),
                our=u'12345',
                entities=[entity]),
            cycles=[
                models.Cycle(
                    name=u'study1-scr',
                    title=u'Study 1 Screening',
                    study=models.Study(
                        name=u'study1',
                        short_title=u'S1',
                        code=u'001',
                        consent_date=date.today() - timedelta(365),
                        title=u'Study 1')),
                models.Cycle(
                    name=u'study2-wk1',
                    title=u'Study 2 Week 1',
                    study=models.Study(
                        name=u'study21',
                        short_title=u'S2',
                        code=u'002',
                        consent_date=date.today() - timedelta(365),
                        title=u'Study 2'))],
            entities=[entity])
        Session.add(visit)

        schema = Session.query(models.Schema).one()
        report = query_report(schema)
        entry = report.one()

        self.assertEquals(entry.site, 'ucsd')
        self.assertEquals(entry.pid, '12345')
        self.assertIsNone(entry.enrollment)
        self.assertItemsEqual(
            entry.cycles.split(','),
            ['study1-scr', 'study2-wk1'])
        self.assertEquals(entry.collect_date, date.today())


class TestDumpQuery(IntegrationFixture):

    def test_unicode(self):
        """
        It should be able to export unicode strings
        """
        from contextlib import closing
        import io
        from sqlalchemy import literal_column, Integer, Unicode
        from occams.clinical import Session
        from occams.clinical.tasks import dump_query, csv

        query = Session.query(
            literal_column(u'"420"', Integer).label(u'anumeric'),
            literal_column(u'"¿Qué pasa?"', Unicode).label(u'astring'),
            )

        with closing(io.BytesIO()) as fp:
            dump_query(fp, query)
            fp.seek(0)
            rows = [r for r in csv.reader(fp)]

        self.assertItemsEqual(['anumeric', 'astring'], rows[0])
        self.assertItemsEqual([u'420', u'¿Qué pasa?'], rows[1])


class TestDumpCodeBook(IntegrationFixture):

    def test_header(self):
        """
        It should have the standard codebook header.
        """
        from contextlib import closing
        import io
        from occams.clinical.tasks import dump_codebook, csv

        with closing(io.BytesIO()) as fp:
            dump_codebook(fp, u'does_no_exist')
            fp.seek(0)
            rows = [r for r in csv.reader(fp)]

        self.assertEquals(rows[0], [
            'form_name',
            'form_title',
            'form_publish_date',
            'field_name',
            'field_title',
            'field_description',
            'field_is_required',
            'field_is_collection',
            'field_type',
            'field_choices',
            'field_order'])

    def test_ignore_retract_data(self):
        """
        It should not include retracted forms
        """
        from contextlib import closing
        from datetime import date, timedelta
        import io
        from occams.clinical import models, Session
        from occams.clinical.tasks import dump_codebook, csv

        self.add_user('joe')
        Session.add_all([
            models.Schema(
                name=u'sample',
                title=u'Sample',
                publish_date=date.today() - timedelta(10),
                attributes={
                    'myvar': models.Attribute(
                        section=models.Section(name='foo', title=u''),
                        name=u'myvar',
                        title=u'My Var',
                        type=u'string',
                        order=0)
                }),
            models.Schema(
                name=u'sample',
                title=u'Sample v2',
                publish_date=date.today(),
                retract_date=date.today(),
                sections=[
                    models.Section(
                        name='foo',
                        title=u'',
                        attributes={
                            'myvar': models.Attribute(
                                name=u'myvar',
                                title=u'My Updated Variable',
                                type=u'string',
                                order=0)
                        })])])

        with closing(io.BytesIO()) as fp:
            dump_codebook(fp, u'sample')
            fp.seek(0)
            rows = [r for r in csv.reader(fp)]
            self.assertItemsEqual(
                ['sample', 'Sample', str(date.today() - timedelta(10)),
                 'myvar', 'My Var', '',
                 'False', 'False', 'string', '', '0'],
                rows[1])

    def test_ignore_with_ids(self):
        """
        It should only include specified ids
        """
        from contextlib import closing
        from datetime import date, timedelta
        import io
        from occams.clinical import models, Session
        from occams.clinical.tasks import dump_codebook, csv

        self.add_user('joe')
        Session.add_all([
            models.Schema(
                name=u'sample',
                title=u'Sample',
                publish_date=date.today() - timedelta(10),
                attributes={
                    'myvar': models.Attribute(
                        section=models.Section(name='foo', title=u''),
                        name=u'myvar',
                        title=u'My Var',
                        type=u'string',
                        order=0)
                }),
            models.Schema(
                name=u'sample',
                title=u'Sample v2',
                publish_date=date.today(),
                attributes={
                    'myvar': models.Attribute(
                        section=models.Section(name='foo', title=u''),
                        name=u'myvar',
                        title=u'My Updated Variable',
                        type=u'string',
                        order=0)
                })])

        id = (
            Session.query(models.Schema)
            .filter_by(publish_date=date.today())
            .one()
            .id)

        with closing(io.BytesIO()) as fp:
            dump_codebook(fp, u'sample', id)
            fp.seek(0)
            rows = [r for r in csv.reader(fp)]
            self.assertItemsEqual(
                ['sample', 'Sample v2', str(date.today()),
                 'myvar', 'My Updated Variable', '',
                 'False', 'False', 'string', '', '0'],
                rows[1])

    def test_with_choices(self):
        from contextlib import closing
        from datetime import date, timedelta
        import io
        from occams.clinical import models, Session
        from occams.clinical.tasks import dump_codebook, csv

        self.add_user('joe')
        Session.add_all([
            models.Schema(
                name=u'sample',
                title=u'Sample',
                publish_date=date.today() - timedelta(10),
                attributes={
                    'myvar': models.Attribute(
                        section=models.Section(name='foo', title=u''),
                        name=u'myvar',
                        title=u'My Var',
                        type=u'string',
                        order=0,
                        choices=[
                            models.Choice(
                                name=u'000', title=u'Cheese', order=0),
                            models.Choice(
                                name=u'001', title=u'Salami', order=1),
                            ])
                })])

        with closing(io.BytesIO()) as fp:
            dump_codebook(fp, u'sample')
            fp.seek(0)
            rows = [r for r in csv.reader(fp)]
            self.assertItemsEqual(
                ['sample', 'Sample', str(date.today() - timedelta(10)),
                 'myvar', 'My Var', '000 - Cheese\r001 - Salami',
                 'False', 'False', 'string', '', '0'],
                rows[1])
