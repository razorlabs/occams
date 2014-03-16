import logging
import pkg_resources

log = logging.getLogger(__name__)

__version__ = pkg_resources.require(__name__)[0].version
