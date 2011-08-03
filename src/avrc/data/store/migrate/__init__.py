import os.path
import migrate.versioning.api
import migrate.exceptions

from avrc.data.store.model import Model


REPOSITORY = os.path.dirname(__file__)


def install(engine):
    """ 
    Install the databases.
    This method will setup the database models using the specified engine
    bind. This is simply a convenience method for creating the database
    tables as well as keeping this module self-contained.

    Arguments:
        ``engine``: An SQLAlchemy engine object.
    """
    url = str(engine.url)

    try:
        migrate.versioning.api.db_version(url, REPOSITORY)
    except migrate.exceptions.DatabaseNotControlledError:
        Model.metadata.create_all(engine)

        # Since it's a fresh install, start at repository version
        version = migrate.versioning.api.version(REPOSITORY)
        migrate.versioning.api.version_control(url, REPOSITORY, version)


def legacy(engine):
    """ 
    Helper method for the sole purpose of putting a legacy database under
    version control. Once under version control, sync may be called.
    """
    url = str(engine.url)

    try:
        migrate.versioning.api.version_control(url, REPOSITORY)
    except migrate.exceptions.DatabaseAlreadyControlledError:
        pass


def sync(engine, version=None):
    """ 
    Synchronizes the version of the current model to the live database
    model.
    
    This method assumes that the database has already been previously
    installed. Since there was not version control previously, if the 
    database is not tagged then it will assume version 0 and try to
    upgrade.
    """
    url = str(engine.url)
    live_version = None

    if version is not None:
        target_version = version
    else:
        target_version = migrate.versioning.api.version(REPOSITORY)

    try:
        migrate.versioning.api.version_control(url, REPOSITORY)
        live_version = 0
    except migrate.exceptions.DatabaseAlreadyControlledError:
        live_version = int(migrate.versioning.api.db_version(url, REPOSITORY))

    if live_version != target_version:
        action = None
        if target_version > live_version:
            action = migrate.versioning.api.upgrade
        elif target_version < live_version:
            action = migrate.versioning.api.downgrade

        action(url, REPOSITORY, target_version)
