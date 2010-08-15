"""
This package contains all bootstrap classes that will be pre-loaded with
each data store.
"""

from zope.interface import Interface
import zope.schema

class ISubject(Interface):
    """
    A subject that that will be associated with attributes. This will also
    serve as a way for both Internal and Accessible data to communicate
    about a subject.
    """

    id = zope.schema.Int(
        title=_(u"Identification Number"),
        description=_(u"")
        )

class IReference(Interface):
    """
    An reference identifier for a subject. This object is intended for legacy
    identifiers from previous systems.
    """

    name = zope.schema.TextLine(
        title=_(u"Name"),
        description=_(u"The name of the reference.")
        )

    number = zope.schema.TextLine(
        title=_(u"Number"),
        description=_("The number given to the subject under the reference.")
        )