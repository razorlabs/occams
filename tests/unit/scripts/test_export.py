try:
    import unitest2 as unittest
except ImportError:
    import unittest


class PrintListTestCase(unittest.TestCase):

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
        self.engine_patch = \
            mock.patch('occams.studies.scripts.export.create_engine').start()
        self.configure_patch = \
            mock.patch('occams.studies.Session.configure').start()

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
        from occams.studies.scripts.export import main
        return main

    def makePlan(self):
        from sqlalchemy import literal_column
        from occams.studies.exports.plan import ExportPlan
        from occams.studies import Session

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
        plan = self.makePlan()
        # force list_all to return only the test form
        with mock.patch('occams.studies.exports.list_all',
                        return_value={plan.name: plan}):
            cmd = self.getCommand()
            cmd([None, '--db', 'fake://', '--list'])
            output = self.getOutput()
            self.assertIn(plan.name, output)

    def test_print_list_with_private(self):
        """
        It should expose the fact that there are private-data plans
        """
        import mock
        plan = self.makePlan()
        plan.has_private = True
        # force list_all to return only the test form
        with mock.patch('occams.studies.exports.list_all',
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
        with mock.patch('occams.studies.exports.list_all',
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
        from occams.studies.exports.codebook import FILE_NAME
        plan = self.makePlan()
        # force list_all to return only the test form
        with mock.patch('occams.studies.exports.list_all',
                        return_value={plan.name: plan}):
            cmd = self.getCommand()
            cmd([None, '--db', 'fake://', '--dir', self.dir, '--all'])
            files = os.listdir(self.dir)
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
        with mock.patch('occams.studies.exports.list_all',
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
        with mock.patch('occams.studies.exports.list_all',
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
        with mock.patch('occams.studies.exports.list_all',
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
        with mock.patch('occams.studies.exports.list_all',
                        return_value={plan.name: plan}):
            cmd = self.getCommand()
            cmd([None, '--db', 'fake://', '--dir', self.dir, plan.name])
            self.assertIn(plan.file_name, os.listdir(self.dir))

    def test_make_export_nothing_specified(self):
        """
        It should quit with an error message if no option is specified
        """
        import mock
        plan = self.makePlan()
        # force list_all to return only the test form
        with self.assertRaises(SystemExit):
            with mock.patch('occams.studies.exports.list_all',
                            return_value={plan.name: plan}):
                cmd = self.getCommand()
                cmd([None, '--db', 'fake://', '--dir', self.dir])
