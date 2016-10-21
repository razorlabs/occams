import logging
import pkg_resources

from . import models

log = logging.getLogger(__name__)

__version__ = pkg_resources.require(__name__)[0].version


def initdb(connectable):
    assert 'blame' in connectable.info, 'Need someone to blame!'
    models.DataStoreModel.metadata.create_all(connectable)


def includeme(config):
    """
    OCCAMS Application init-handler
    Do nothing since this app is a standalone utility
    """
