import logging
import pkg_resources

log = logging.getLogger(__name__)

__version__ = pkg_resources.require(__name__)[0].version


def includeme(config):
    """
    OCCAMS Application init-handler
    Do nothing since this app is a standalone utility
    """
