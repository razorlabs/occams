""" Data Definition Library

    Notes:
        * Most of the code for this model follows the DS-0 specification,
          which is the initial release code. Some entities are starting to
          be migrated to the DS-1 specification which specifies that all
          new tables should have a create/modify/remove columns for dates
          as well as user id numbers that invoked the data. Since there is no
          user system currently in place the user columns will be ignored.
          The date columns, on the other hand, will be updated. remove_date is
          the new is_active column.

"""

import os.path

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

from zope.deprecation import deprecate

import migrate.versioning.api
try:
    from migrate.versioning.exceptions import DatabaseAlreadyControlledError
    from migrate.versioning.exceptions import DatabaseNotControlledError
except ImportError:
    from migrate.exceptions import DatabaseAlreadyControlledError
    from migrate.exceptions import DatabaseNotControlledError
# Base class for declarative syntax on our models
Model = declarative_base()

# To avoid circular dependencies, import models after base has been defined
from avrc.data.store.model.clinical import *
from avrc.data.store.model.eavcr import *
from avrc.data.store.model.medication import *
from avrc.data.store.model.symptom import *

import avrc.data.store.upgrades


metadata = Model.metadata


type_names = (
    u'integer',
    u'string', u'text' ,
    u'boolean',
    u'real',
    u'date', u'datetime', u'time',
    )


@deprecate('model(engine) has been deprecated, use install(engine)')
def setup(engine):
    """ Sets up the database tables.
    """
    install(engine)


def install(engine):
    """ Install the databases.
        This method will setup the database models using the specified engine
        bind. This is simply a convenience method for creating the database
        tables as well as keeping this module self-contained.

        Arguments:
            ``engine``: An SQLAlchemy engine object.
    """
    url = str(engine.url)
    repository = os.path.dirname(avrc.data.store.upgrades.__file__)

    try:
        migrate.versioning.api.db_version(url, repository)
    except DatabaseNotControlledError:
        Model.metadata.create_all(engine)

        for type_name in type_names:
            engine.execute(Type.__table__.insert().values(title=type_name))

        # Since it's a fresh install, start at repository version
        version = migrate.versioning.api.version(repository)
        migrate.versioning.api.version_control(url, repository, version)


def legacy(engine):
    """ Helper method for the sole purpose of putting a legacy database under
        version control. Once under version control, sync may be called.
    """
    url = str(engine.url)
    repository = os.path.dirname(avrc.data.store.upgrades.__file__)

    try:
        migrate.versioning.api.version_control(url, repository)
    except DatabaseAlreadyControlledError:
        pass


def sync(engine):
    """ Synchronizes the version of the current model to the live database
        model.
        
        This method assumes that the database has already been previously
        installed. Since there was not version control previously, if the 
        database is not tagged then it will assume version 0 and try to
        upgrade.
    """
    url = str(engine.url)
    repository = os.path.dirname(avrc.data.store.upgrades.__file__)
    repository_version = migrate.versioning.api.version(repository)
    live_version = None

    try:
        migrate.versioning.api.version_control(url, repository)
        live_version = 0
    except DatabaseAlreadyControlledError:
        live_version = int(migrate.versioning.api.db_version(url, repository))

    if live_version != repository_version:
        action = None
        if repository_version > live_version:
            action = migrate.versioning.api.upgrade
        elif repository_version < live_version:
            action = migrate.versioning.api.downgrade

        action(url, repository, repository_version)
