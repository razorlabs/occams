import pytest


class TestIncludeme:

    def test_settings(self, config):
        """
        It should be able to sanitize export-specific settings
        """
        from tests.conftest import REDIS_URL
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

        config.registry.settings.update(input)
        config.include('occams_studies.tasks')
        for key in input.keys():
            assert config.registry.settings[key] == expected[key]


@pytest.mark.usefixtures('celery')
class TestMakeExport:

    def test_zip(self):
        """
        It should generate a zip file containing the specified contents
        """
        from zipfile import ZipFile
        from occams.celery import Session
        from occams_studies import models, tasks

        owner = models.User(key=u'joe')
        Session.info['blame'] = owner
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
        export = Session.merge(export)
        with ZipFile(export.path, 'r') as zfp:
            file_names = zfp.namelist()

        assert sorted(['pid.csv', 'codebook.csv']) == sorted(file_names)
