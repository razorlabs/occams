""" Data Definition Library

    The entities defined within this module are the foundation for the EAV/CR
    framework implementation for use in the data store utility. Not that these
    table definitions are independent of the interfaces defined by this package.
    The reason for this is so that these models can be reused differently
    in a separate script/application  if need be. Though, importing this module
    can also result in circumventing the entire purpose of the package as well.
    Thus, because the are not implementations of the the interfaces, they can
    be used freely in the utility implementations instead.

    More information on EAV/CR:
    http://www.ncbi.nlm.nih.gov/pmc/articles/PMC61391/

    Note that the models defined in this module are mapped to a database.
    Therefore, great care should be taken when updating this file, as it may
    cause live systems to fall out of sync.

    TODO: (mmartinez)
        * Cascade update/deletes
"""

from sqlalchemy.ext.declarative import declarative_base


# Base class for declarative syntax on our models
Model = declarative_base()


from avrc.data.store.model.arv import *
from avrc.data.store.model.clinical import *
from avrc.data.store.model.eavcr import *
from avrc.data.store.model.lab import *
from avrc.data.store.model.symptom import *


def setup(engine):
    """ This method will setup the database models using the specified engine
        bind. This is simply a convenience method for creating the database
        tables as well as keeping this module self-contained

        Arguments:
            engine: A sqlalchemy engine object.

        Returns:
            N\A
    """

    Model.metadata.create_all(bind=engine, checkfirst=True)
