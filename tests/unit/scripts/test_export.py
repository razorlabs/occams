import pytest


@pytest.fixture
def plan(dbsession):
    from sqlalchemy import literal_column
    from occams.exports.plan import ExportPlan

    class DummyPlan(ExportPlan):
        name = 'aform'
        title = 'A Form'

        def codebook(self):
            return []

        def data(self, *args, **kw):
            return self.dbsession.query(
                literal_column("'blah'").label('dummy')
            )

    return DummyPlan(dbsession)


class TestPrintList:

    # TODO: need to figure out how to ensure the export methods
    #       were passed a dbsession

    @pytest.fixture(autouse=True)
    def initialize(self, request, dbsession, req):
        import tempfile
        import shutil
        import mock

        req.registry.settings['studies.export.plans'] = []

        # Don't configure the logging
        self.setup_logging_patch = mock.patch(
            'occams.scripts.export.setup_logging',
        ).start()

        # Don't configure the session since we already did that in the
        # the package setup
        self.bootstrap_patch = mock.patch(
            'occams.scripts.export.bootstrap',
            return_value={
                'request': req,
                'registry': req.registry,
            }).start()

        self.dir = tempfile.mkdtemp()

        def finalize():
            mock.patch.stopall()
            shutil.rmtree(self.dir)

        request.addfinalizer(finalize)

    def _call_fut(self, *args, **kw):
        # Override stdout so we can inspect output
        import sys
        import io
        from occams.scripts.export import main as cmd
        _saved_stdout = sys.stdout
        sys.stdout = io.StringIO()
        cmd(*args, **kw)
        output = sys.stdout.getvalue()
        sys.stdout = _saved_stdout
        return output

    def test_print_list(self, dbsession, plan):
        """
        It should be able to print a listing of exportables
        """
        import mock
        # force list_all to return only the test form
        with mock.patch('occams.exports.list_all',
                        return_value={plan.name: plan}):
            output = self._call_fut([None, '--config', 'fake.ini', '--list'])
            assert plan.name in output

    def test_print_list_with_private(self, plan):
        """
        It should expose the fact that there are private-data plans
        """
        import mock
        plan.has_private = True
        # force list_all to return only the test form
        with mock.patch('occams.exports.list_all',
                        return_value={plan.name: plan}):
            output = self._call_fut([None, '--config', 'fake.ini', '--list'])
            assert '*' in output

    def test_print_list_with_rand(self, plan):
        """
        It should expose the fact that there are randomization plans
        """
        import mock
        plan.has_rand = True
        # force list_all to return only the test form
        with mock.patch('occams.exports.list_all',
                        return_value={plan.name: plan}):
            output = self._call_fut([None, '--config', 'fake.ini', '--list'])
            assert '*' in output

    def test_make_export_all(self, dbsession, plan):
        """
        It should be able to export data for all plans
        """
        import os
        import mock
        from occams.exports.codebook import FILE_NAME
        # force list_all to return only the test form
        with mock.patch('occams.exports.list_all',
                        return_value={plan.name: plan}):
            self._call_fut(
                [None, '--config', 'fake.ini', '--dir', self.dir, '--all'])
            files = os.listdir(self.dir)
            assert plan.file_name in files
            assert FILE_NAME in files

    def test_make_export_private(self, plan):
        """
        It should be able to export only private data
        """
        import os
        import mock
        # force list_all to return only the test form
        with mock.patch('occams.exports.list_all',
                        return_value={plan.name: plan}):
            self._call_fut(
                [None, '--config', 'fake.ini', '--dir', self.dir, '--all-private'])
            assert plan.file_name not in os.listdir(self.dir)

            plan.has_private = True
            self._call_fut(
                [None, '--config', 'fake.ini', '--dir', self.dir, '--all-private'])
            assert plan.file_name in os.listdir(self.dir)

    def test_make_export_public(self, plan):
        """
        It should be able to export only public data
        """
        import os
        import mock
        # force list_all to return only the test form
        with mock.patch('occams.exports.list_all',
                        return_value={plan.name: plan}):
            plan.has_private = True
            self._call_fut(
                [None, '--config', 'fake.ini', '--dir', self.dir, '--all-public'])
            assert plan.file_name not in os.listdir(self.dir)

            plan.has_private = False
            self._call_fut(
                [None, '--config', 'fake.ini', '--dir', self.dir, '--all-public'])
            assert plan.file_name in os.listdir(self.dir)

    def test_make_export_rand(self, plan):
        """
        It should be able to export only randomization data
        """
        import os
        import mock
        # force list_all to return only the test form
        with mock.patch('occams.exports.list_all',
                        return_value={plan.name: plan}):
            self._call_fut(
                [None, '--config', 'fake.ini', '--dir', self.dir, '--all-rand'])
            assert plan.file_name not in os.listdir(self.dir)

            plan.has_rand = True
            self._call_fut(
                [None, '--config', 'fake.ini', '--dir', self.dir, '--all-rand'])
            assert plan.file_name in os.listdir(self.dir)

    def test_make_export_by_name(self, plan):
        """
        It should be able to export only specified named
        """
        import os
        import mock
        # force list_all to return only the test form
        with mock.patch('occams.exports.list_all',
                        return_value={plan.name: plan}):
            self._call_fut(
                [None, '--config', 'fake.ini', '--dir', self.dir, plan.name])
            assert plan.file_name in os.listdir(self.dir)

    def test_make_export_nothing_specified(self, plan):
        """
        It should quit with an error message if no option is specified
        """
        import mock
        # force list_all to return only the test form
        with pytest.raises(SystemExit):
            with mock.patch('occams.exports.list_all',
                            return_value={plan.name: plan}):
                self._call_fut([None, '--config', 'fake.ini', '--dir', self.dir])

    def test_make_export_atomic(self, plan):
        """
        It should allow atomic generating of data files
        """
        import os
        import mock
        dest_dir = os.path.join(self.dir, 'myfiles')
        # force list_all to return only the test form
        with mock.patch('occams.exports.list_all',
                        return_value={plan.name: plan}):
            self._call_fut(
                [None, '--config', 'fake.ini', '--all', '--dir', dest_dir,
                    '--atomic'])
        assert os.path.islink(dest_dir), 'Not a symlink'

    def test_make_export_atomic_remove_old(self, plan):
        """
        It should cleanup old data directories from a previous atomic run.
        """
        import os
        import mock
        old_dir = os.path.join(self.dir, 'oldpath')
        dest_dir = os.path.join(self.dir, 'myfiles')
        os.makedirs(old_dir)
        os.symlink(old_dir, dest_dir)
        # force list_all to return only the test form
        with mock.patch('occams.exports.list_all',
                        return_value={plan.name: plan}):
            self._call_fut(
                [None, '--config', 'fake.ini', '--all', '--dir', dest_dir,
                    '--atomic'])
        assert not os.path.exists(old_dir), 'Was not removed'

    def test_make_export_create_directory(self):
        """
        It should auto create the destination directory if it doesn't exist.
        """
        import os
        import mock
        dest_dir = os.path.join(self.dir, 'myfiles')
        # force list_all to return only the test form
        with mock.patch('occams.exports.list_all',
                        return_value={}):
            self._call_fut(
                [None, '--config', 'fake.ini', '--all', '--dir', dest_dir])
        assert os.path.isdir(dest_dir)
