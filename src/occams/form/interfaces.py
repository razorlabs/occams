import zope.interface
import zope.schema

from avrc.data.store.interfaces import IDataBaseItem

from occams.form import MessageFactory as _


class IOccamsBrowserView(zope.interface.Interface):
    """
    Marker inteface for views of this plugin
    """

class IFormSummary(zope.interface.Interface):
    """
    Form summary for listing purposes.
    """

    title = zope.schema.TextLine(
        title=_(u'Title'),
        description=_(u'Human-readable title'),
        readonly=True,
        )

    fieldCount = zope.schema.Int(
        title=_(u'# Fields'),
        description=_(
            u'Number of fields in the form, not including subform fields.'
            ),
        readonly=True,
        )

    revisionCount = zope.schema.Int(
        title=_(u'# Revisions'),
        description=_(u'Number of times the form has been revised'),
        readonly=True,
        )

    currentVersion = zope.schema.Date(
        title=_(u'Version'),
        description=_(u'Current version number'),
        readonly=True,
        )

    createdOn = zope.schema.Date(
        title=_(u'Created'),
        description=_(u'The date the form was created'),
        readonly=True,
        )


class IRepository(zope.interface.Interface):
    """
    Form repository entry point.
    Objects of this type offer services for managing forms as well as
    form EAV tables from ``avrc.data.store.DataStore``
    """

    session = zope.schema.Choice(
        title=_(u'Database Session'),
        description=_(
            u'Select from one of the registered database sessions '
            u'to use as the form repository. Note this will install all '
            u'SQL tables necessary for managing forms. '
            u'See product documentation to ensure there are no name collisions.'
            ),
        vocabulary=u'occams.form.AvailableSessions',
        required=True,
        default=None,
        )


class IDataBaseItemContext(zope.interface.Interface):
    """
    A wrapper context for DataStore schemata so they are traversable
    """

    item = zope.schema.Object(
        title=_(u'The schema this context wraps'),
        schema=IDataBaseItem,
        readonly=True
        )


class ISchemaContext(IDataBaseItemContext):
    pass

class IFieldContext(IDataBaseItemContext):
    pass

