import zope.interface
import zope.schema
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

from grokcore.component.interfaces import IContext
from plone.directives import form

from avrc.data.store.interfaces import IDataBaseItem

from occams.form import MessageFactory as _


typesVocabulary = SimpleVocabulary(terms=[
        SimpleTerm(value=zope.schema.Bool, token='boolean', title=_(u'Boolean')),
        SimpleTerm(value=zope.schema.Decimal, token='decimal', title=_(u'Decimal')),
        SimpleTerm(value=zope.schema.Int, token='integer', title=_(u'Integer')),
        SimpleTerm(value=zope.schema.Date, token='date', title=_(u'Date')),
        SimpleTerm(value=zope.schema.Datetime, token='datetime', title=_(u'Date and Time')),
        SimpleTerm(value=zope.schema.TextLine, token='string', title=_(u'Text')),
        SimpleTerm(value=zope.schema.Text, token='text', title=_(u'Paragraph')),

        SimpleTerm(value=zope.schema.Object, token='object', title=_(u'Field Set')),
    ])


class IOccamsFormComponent(zope.interface.Interface):
    """
    Marker interfaces for interfaces of this plug-in
    """


class IOccamsBrowserView(IOccamsFormComponent):
    """
    Marker inteface for views of this plugin
    """


class IFormSummary(IOccamsFormComponent):
    """
    Form summary for listing purposes.
    """

    name = zope.schema.ASCIILine(
        title=_(u'Name'),
        description=_(u'Machine name'),
        readonly=True
        )

    title = zope.schema.TextLine(
        title=_(u'Title'),
        description=_(u'Human-readable title'),
        readonly=True,
        )

    fieldCount = zope.schema.Int(
        title=_(u'Fields'),
        description=_(
            u'Number of fields in the form, not including subform fields.'
            ),
        readonly=True,
        )

    revisionCount = zope.schema.Int(
        title=_(u'Revisions'),
        description=_(u'Number of times the form has been published'),
        readonly=True,
        )

    changeCount = zope.schema.Int(
        title=_(u'Changes'),
        description=_(u'Number of times the form has been modified'),
        readonly=True,
        )

    currentVersion = zope.schema.Date(
        title=_(u'Current'),
        description=_(u'Current revision'),
        readonly=True,
        )

    createdOn = zope.schema.Date(
        title=_(u'Created'),
        description=_(u'The date the form was created'),
        readonly=True,
        )


class IDataBaseItemContext(IOccamsFormComponent, IContext):
    """
    A wrapper context for DataStore entries so they are traversable.
    This allows a wrapped entry to comply with the Acquisition machinery
    in Plone.
    """

    item = zope.schema.Object(
        title=_(u'The schema this context wraps'),
        schema=IDataBaseItem,
        readonly=True
        )


class ISchemaContext(IDataBaseItemContext):
    """
    Context for DataStore Schema wrapper.
    """


class IEntityContext(IDataBaseItemContext):
    """
    Context for DataStore Entity wrapper.
    """


class IAttributeContext(IDataBaseItemContext):
    """
    Context for DatataStore Attribute wrapper.
    """


class IFormSummaryGenerator(zope.interface.Interface):
    """
    Generator of ``IFormSummary`` results from a database
    """

    def getItems(session):
        """
        Returns a full listing of ``IFormSummary`` objects in the context
        """


class IRepository(IOccamsFormComponent, form.Schema):
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
