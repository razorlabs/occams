import os.path

import migrate.versioning.api
import migrate.exceptions

from occams.roster.upgrades import migrate as repository
from occams.roster import Session
from occams.roster import model


def import_various(context):
    u"""
    GenericSetup conventional handle for importing miscellaneous steps.
    """
    if context.readDataFile('occams-roster.txt') is not None:
        portal = context.getSite()
        setup_database(portal)


def setup_database(portal):
    session = Session()
    engine = session.bind
    url = str(engine.url)
    repository_path = os.path.dirname(repository.__file__)

    try:
        migrate.versioning.api.db_version(url, repository_path)
    except migrate.exceptions.DatabaseNotControlledError:
        model.RosterModel.metadata.create_all(engine)
        # since it's a fresh install, start at repository version
        version = migrate.versioning.api.version(repository_path)
        migrate.versioning.api.version_control(url, repository_path, version)

