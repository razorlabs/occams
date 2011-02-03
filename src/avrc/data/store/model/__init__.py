""" Data Definition Library

    Note that the models defined in this module are mapped to a database.
    Therefore, great care should be taken when updating these files, as it may
    cause live systems to fall out of sync.

    TODO: (mmartinez)
        * Cascade update/deletes
"""

from sqlalchemy.ext.declarative import declarative_base


# Base class for declarative syntax on our models
Model = declarative_base()

# To avoid circular dependencies, import models after base has been defined
from avrc.data.store.model.arv import *
from avrc.data.store.model.clinical import *
from avrc.data.store.model.eavcr import *
from avrc.data.store.model.lab import *
from avrc.data.store.model.symptom import *


def setup(engine):
    """ Sets up the database tables.

        This method will setup the database models using the specified engine
        bind. This is simply a convenience method for creating the database
        tables as well as keeping this module self-contained.

        Arguments:
            ``engine``: An SQLAlchemy engine object.
    """

    Model.metadata.create_all(bind=engine, checkfirst=True)
