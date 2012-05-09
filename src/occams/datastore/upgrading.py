"""
SQLAlchemy-migrate tools
"""

import os.path
import migrate.versioning.api
import migrate.exceptions


def install(metadata, engine, repository):
    """
    Install the databases.
    This method will setup the database models using the specified engine
    bind. This is simply a convenience method for creating the database
    tables as well as keeping this module self-contained.

    Arguments
        ``metadata``
            The table metadata to install
        ``engine``
            Target SQLAlchemy egnine connection
        ``repository``
            The path or package where the repository lives

    """
    url = str(engine.url)

    if not isinstance(repository, basestring):
        repository = os.path.dirname(repository.__file__)

    try:
        migrate.versioning.api.db_version(url, repository)
    except migrate.exceptions.DatabaseNotControlledError:
        # Create database from scratch and tag as most recent version
        metadata.create_all(engine)
        version = migrate.versioning.api.version(repository)
        migrate.versioning.api.version_control(url, repository, version)


def sync(metadata, engine, repository, version=None):
    """
    Synchronizes the version of the current model to the live database
    model.

    This method assumes that the database has already been previously
    installed. Since there was not version control previously, if the
    database is not tagged then it will assume version 0 and try to
    upgrade.

    Arguments
        ``metadata``
            The table metadata to install
        ``engine``
            Target SQLAlchemy engine connection
        ``repository``
            The path or package where the repository lives
        ``version``
            (Optional) The target version to sync to, default is current in
            the repository
    """
    url = str(engine.url)

    if version is None:
        version = migrate.versioning.api.version(repository)

    if not isinstance(repository, basestring):
        repository = os.path.dirname(repository.__file__)

    try:
        migrate.versioning.api.version_control(url, repository)
    except migrate.exceptions.DatabaseAlreadyControlledError:
        live_version = int(migrate.versioning.api.db_version(url, repository))
    else:
        live_version = 0
    finally:
        if version > live_version:
            migrate.versioning.api.upgrade(url, repository, version)
        elif version < live_version:
            migrate.versioning.api.downgrade(url, repository, version)
