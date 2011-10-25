import zope.interface
import zope.schema

from grokcore.component.interfaces import IContext
from plone.directives import form
from z3c.form.interfaces import IAddForm
from z3c.form.interfaces import IEditForm

from avrc.data.store.interfaces import IDataBaseItem

from occams.form import MessageFactory as _

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


class IChangeset(IOccamsFormComponent, form.Schema):
    """
    Changes to a form before they are sent to DataStore.
    This allows a workflow process to the used for updating forms.
    """

    form.omitted('formName')
    form.no_omit(IAddForm, 'formName')
    formName = zope.schema.Choice(
        title=_(u'Form'),
        description=_(u'The form to be modified'),
        vocabulary=u'occams.form.Forms'
        )

    form.omitted(IAddForm, 'source')
    source = zope.schema.Text(
        title=_(u'Form Source'),
        description=_(u'Save changes to a form before committing'),
        )
