from zope.interface import Interface
import zope.schema
from hive.roster import MessageFactory as _


class Error(Exception):
    """
    Base Error
    """

class NotFoundError(Error):
    """
    Identifier not found
    """


class IIdentifier(Interface):
    """
    An OUR number description.
    """

    value = zope.schema.Int(
        title=_(u'Raw OUR number'),
        required=True,
        )

    def __str__():
        """
        Formats raw OUR number to human readable.
        """

class ISite(Interface):
    """
    Represents a site that is using this registry. It will be useful for
    when tracking which sites are creating identifiers.
    """

    title = zope.schema.TextLine(
        title=_(u'Site Title'),
        description=_(u'The name of the site, for our records.'),
        required=True,
        )


class IRegistry(Interface):
    """
    Represents a component that will be in charge of creating identifiers as
    well as retiring them when they are no longer in use.
    """

    def create():
        """
        Creates an identifier.
        """
