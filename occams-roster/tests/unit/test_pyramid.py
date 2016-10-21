import pytest


class TestPyramidIntegration:
    """
    Verifies proper integration with Pyramid (if available)
    """

    def test_includeme(self, config):
        """
        It should register the database
        """
        from sqlalchemy import orm
        from tempfile import NamedTemporaryFile
        with NamedTemporaryFile() as fp:
            url = 'sqlite:///' + fp.name
            config.registry.settings['roster.db.url'] = url
            config.registry['db_sessionmaker'] = orm.sessionmaker()
            config.include('occams_roster')
