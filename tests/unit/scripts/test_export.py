from tests import IntegrationFixture


class PrintListTestCase(IntegrationFixture):

    def setUp(self):
        import tempfile
        import sys
        import mock
        from six.moves import StringIO

        # Override stdout so we can inspect output
        self._saved_stdout = sys.stdout
        sys.stdout = StringIO()

        # Don't configure the session since we already did that in the
        # the package setup
        self.create_engine_patch = \
            mock.patch('occams_studies.scripts.export.create_engine').start()
        self.session_configure_patch = \
            mock.patch('occams_studies.Session.configure').start()
        self.engine_from_config_patch = \
            mock.patch('occams_studies.scripts.export.engine_from_config')\
            .start()

        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        import sys
        import mock
        sys.stdout = self._saved_stdout
        mock.patch.stopall()
        shutil.rmtree(self.dir)

    def getOutput(self):
        import sys
        return sys.stdout.getvalue()

    def getCommand(self):
        from occams_studies.scripts.export import main
        return main

    def makePlan(self):
        from sqlalchemy import literal_column
        from occams_studies.exports.plan import ExportPlan
        from occams_studies import Session

        class DummyPlan(ExportPlan):
            name = u'aform'
            title = u'A Form'

            def codebook(self):
                return []

            def data(self, *args, **kw):
                return Session.query(literal_column("'blah'").label('dummy'))

        return DummyPlan()

    def test_print_list(self):
        """
        It should be able to print a listing of exportables
        """
        import mock
        from occams_studies import Session
        plan = self.makePlan()
        # force list_all to return only the test form
        with mock.patch('occams_studies.exports.list_all',
                        return_value={plan.name: plan}) as patch:
            cmd = self.getCommand()
            cmd([None, '--db', 'fake://', '--list'])
            output = self.getOutput()
            patch.assert_called_once_with(Session)
            self.assertIn(plan.name, output)

    def test_print_list_with_private(self):
        """
        It should expose the fact that there are private-data plans
        """
        import mock
        plan = self.makePlan()
        plan.has_private = True
        # force list_all to return only the test form
        with mock.patch('occams_studies.exports.list_all',
                        return_value={plan.name: plan}):
            cmd = self.getCommand()
            cmd([None, '--db', 'fake://', '--list'])
            output = self.getOutput()
            self.assertIn('*', output)

    def test_print_list_with_rand(self):
        """
        It should expose the fact that there are randomization plans
        """
        import mock
        plan = self.makePlan()
        plan.has_rand = True
        # force list_all to return only the test form
        with mock.patch('occams_studies.exports.list_all',
                        return_value={plan.name: plan}):
            cmd = self.getCommand()
            cmd([None, '--db', 'fake://', '--list'])
            output = self.getOutput()
            self.assertIn('*', output)

    def test_make_export_all(self):
        """
        It should be able to export data for all plans
        """
        import os
        import mock
        from occams_studies import Session
        from occams_studies.exports.codebook import FILE_NAME
        plan = self.makePlan()
        # force list_all to return only the test form
        with mock.patch('occams_studies.exports.list_all',
                        return_value={plan.name: plan}) as patch:
            cmd = self.getCommand()
            cmd([None, '--db', 'fake://', '--dir', self.dir, '--all'])
            files = os.listdir(self.dir)
            patch.assert_called_once_with(Session)
            self.assertIn(plan.file_name, files)
            self.assertIn(FILE_NAME, files)

    def test_make_export_private(self):
        """
        It should be able to export only private data
        """
        import os
        import mock
        plan = self.makePlan()
        # force list_all to return only the test form
        with mock.patch('occams_studies.exports.list_all',
                        return_value={plan.name: plan}):
            cmd = self.getCommand()
            cmd([None, '--db', 'fake://', '--dir', self.dir, '--all-private'])
            self.assertNotIn(plan.file_name, os.listdir(self.dir))

            plan.has_private = True
            cmd([None, '--db', 'fake://', '--dir', self.dir, '--all-private'])
            self.assertIn(plan.file_name, os.listdir(self.dir))

    def test_make_export_public(self):
        """
        It should be able to export only public data
        """
        import os
        import mock
        plan = self.makePlan()
        # force list_all to return only the test form
        with mock.patch('occams_studies.exports.list_all',
                        return_value={plan.name: plan}):
            cmd = self.getCommand()
            plan.has_private = True
            cmd([None, '--db', 'fake://', '--dir', self.dir, '--all-public'])
            self.assertNotIn(plan.file_name, os.listdir(self.dir))

            plan.has_private = False
            cmd([None, '--db', 'fake://', '--dir', self.dir, '--all-public'])
            self.assertIn(plan.file_name, os.listdir(self.dir))

    def test_make_export_rand(self):
        """
        It should be able to export only randomization data
        """
        import os
        import mock
        plan = self.makePlan()
        # force list_all to return only the test form
        with mock.patch('occams_studies.exports.list_all',
                        return_value={plan.name: plan}):
            cmd = self.getCommand()
            cmd([None, '--db', 'fake://', '--dir', self.dir, '--all-rand'])
            self.assertNotIn(plan.file_name, os.listdir(self.dir))

            plan.has_rand = True
            cmd([None, '--db', 'fake://', '--dir', self.dir, '--all-rand'])
            self.assertIn(plan.file_name, os.listdir(self.dir))

    def test_make_export_by_name(self):
        """
        It should be able to export only specified named
        """
        import os
        import mock
        plan = self.makePlan()
        # force list_all to return only the test form
        with mock.patch('occams_studies.exports.list_all',
                        return_value={plan.name: plan}):
            cmd = self.getCommand()
            cmd([None, '--db', 'fake://', '--dir', self.dir, plan.name])
            self.assertIn(plan.file_name, os.listdir(self.dir))

    def test_make_export_with_config(self):
        """
        It should be able to export using an app configuration file
        """
        import tempfile
        import mock
        # force list_all to return only the test form
        with tempfile.NamedTemporaryFile() as fp:
            fp.write("""
[app:main]
use = egg:occams
occams.db.url = fake://
""")
            fp.flush()
            with mock.patch('occams_studies.exports.list_all',
                            return_value={}):
                cmd = self.getCommand()
                cmd([None, '--config', fp.name, '--all', '--dir', self.dir])
                self.assertTrue(self.engine_from_config_patch.called)

    def test_make_export_no_connection(self):
        """
        It should require a connection
        """
        with self.assertRaisesRegexp(SystemExit, '.*configuration.*'):
            cmd = self.getCommand()
            cmd([None, '--dir', self.dir])

    def test_make_export_nothing_specified(self):
        """
        It should quit with an error message if no option is specified
        """
        import mock
        plan = self.makePlan()
        # force list_all to return only the test form
        with self.assertRaises(SystemExit):
            with mock.patch('occams_studies.exports.list_all',
                            return_value={plan.name: plan}):
                cmd = self.getCommand()
                cmd([None, '--db', 'fake://', '--dir', self.dir])

    def test_make_export_atomic(self):
        """
        It should allow atomic generating of data files
        """
        import os
        import mock
        plan = self.makePlan()
        dest_dir = os.path.join(self.dir, 'myfiles')
        # force list_all to return only the test form
        with mock.patch('occams_studies.exports.list_all',
                        return_value={plan.name: plan}):
            cmd = self.getCommand()
            cmd([None, '--db', 'fake://', '--all', '--dir', dest_dir,
                '--atomic'])
        self.assertTrue(os.path.islink(dest_dir), 'Not a symlink')

    def test_make_export_atomic_remove_old(self):
        """
        It should cleanup old data directories from a previous atomic run.
        """
        import os
        import mock
        plan = self.makePlan()
        old_dir = os.path.join(self.dir, 'oldpath')
        dest_dir = os.path.join(self.dir, 'myfiles')
        os.makedirs(old_dir)
        os.symlink(old_dir, dest_dir)
        # force list_all to return only the test form
        with mock.patch('occams_studies.exports.list_all',
                        return_value={plan.name: plan}):
            cmd = self.getCommand()
            cmd([None, '--db', 'fake://', '--all', '--dir', dest_dir,
                '--atomic'])
        self.assertFalse(os.path.exists(old_dir), 'Was not removed')

    def test_make_export_create_directory(self):
        """
        It should auto create the destination directory if it doesn't exist.
        """
        import os
        import mock
        dest_dir = os.path.join(self.dir, 'myfiles')
        # force list_all to return only the test form
        with mock.patch('occams_studies.exports.list_all',
                        return_value={}):
            cmd = self.getCommand()
            cmd([None, '--db', 'fake://', '--all', '--dir', dest_dir])
        self.assertTrue(os.path.isdir(dest_dir))
