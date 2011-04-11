""" Data Definition Library

    Notes:
        * Most of the code for this model follows the DS-0 specification,
          which is the initial release code. Some entities are starting to
          be migrated to the DS-1 specification which specifies that all
          new tables should have a create/modify/remove columns for dates
          as well as user ids that invoked the data. Since there is no
          user system currently in place the user columns will be ignored.
          The date colums, on the other hand, will be updated. remove_date is
          the new is_active column.

"""

from sqlalchemy.ext.declarative import declarative_base

from zope.deprecation import deprecate

import migrate.versioning.api
from migrate.versioning.exceptions import DatabaseAlreadyControlledError


# Base class for declarative syntax on our models
Model = declarative_base()

# To avoid circular dependencies, import models after base has been defined
from avrc.data.store.model.clinical import *
from avrc.data.store.model.eavcr import *
from avrc.data.store.model.lab import *
from avrc.data.store.model.medication import *
from avrc.data.store.model.symptom import *

import avrc.data.store.upgrades


__version__ = 004


metadata = Model.metadata


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

    Model.metadata.create_all(bind=engine, checkfirst=True)

    version = __version__
    repository = avrc.data.store.upgrades.__path__[0]
    url = str(engine.url)

    try:
        migrate.versioning.api.version_control(url, repository, version)
    except DatabaseAlreadyControlledError:
        current_version = int(migrate.versioning.api.db_version(url, repository))

        if current_version > version:
            migrate.versioning.api.upgrade(url, repository, version)
        elif current_version < version:
            migrate.versioning.api.downgrade(url.repository, version)
