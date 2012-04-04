from collective.z3cform.datagridfield import DictRow
import zope.interface
import zope.schema
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
import plone.directives.form

from occams.datastore.interfaces import IDataBaseItem
from occams.form import MessageFactory as _


DATA_KEY = 'occams.form'

TEXTAREA_SIZE = 5

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

class IDataStore(zope.interface.Interface):
    """
    Class to get rid of
    """

class IOccamsFormComponent(zope.interface.Interface):
    """
    Marker interfaces for interfaces of this plug-in
    """

class IEditableState(IOccamsFormComponent):
    """
    The human-friendly form for editing possible form states
    """

    name = zope.schema.ASCIILine(
        title=_(u'State label'),
        description=_(
            u'This value is used internally'
            ),
        )

    title = zope.schema.TextLine(
        title=_(u'Title'),
        description=_(u'The displayed name of the state'),
        )

    description = zope.schema.Text(
        title=_(u'Description'),
        description=_(u'A short description about what the state is for.'),
        required=False,
        )


class IEditableForm(IOccamsFormComponent):
    """
    The human-friendly form for edidting a field.
    """

    name = zope.schema.ASCIILine(
        title=_(u'Class Name'),
        description=_(
            u'Internal variable name, this value cannot be changed once it is '
            u'created.'
            ),
        readonly=True,
        )

    title = zope.schema.TextLine(
        title=_(u'Title'),
        description=_(u'The displayed name of the form.'),
        )

    description = zope.schema.Text(
        title=_(u'Description'),
        description=_(u'A short description about what the form is for.'),
        required=False,
        )


class IEditableField(IOccamsFormComponent):
    """
    The human-friendly form for edidting a field.
    """

    # Note we did not make this readonly so that users with superpowers can
    # change it
    name = zope.schema.ASCIILine(
        title=_(u'Variable Name'),
        description=_(
            u'Internal variable name, this value cannot be changed once it is '
            u'created.'
            ),
        )

    title = zope.schema.TextLine(
        title=_(u'Label'),
        description=_(u'The prompt for the user.'),
        )

    description = zope.schema.Text(
        title=_(u'Description'),
        description=_(u'A short description about what this field is for.'),
        required=False,
        )

    order = zope.schema.Int(
        title=_(u'Order'),
        description=_(u'The field\'s order in the form'),
        required=True
        )



class ICollectable(IOccamsFormComponent):

    is_collection = zope.schema.Bool(
        title=_(u'Multiple?'),
        description=_(u'If selected, the user may enter more than one value.'),
        default=False,
        )


class IRequireable(IOccamsFormComponent):

    is_required = zope.schema.Bool(
        title=_(u'Required?'),
        description=_(u'If selected, the user will be required to enter a value.'),
        default=False,
        )


class IEditableChoice(IOccamsFormComponent):

    title = zope.schema.TextLine(
        title=_(u'Displayed Label'),
        )

    value = zope.interface.Attribute(_(u'The value stored for the answer choice'))


class IEditableBooleanChoice(IEditableChoice):

    value = zope.schema.Bool(
        title=_(u'Stored Value'),
        )


class IEditableBooleanField(IEditableField, IRequireable):

    choices = zope.schema.List(
        title=_(u'Configure True/False Labels'),
        value_type=DictRow(schema=IEditableBooleanChoice),
        required=True,
        )


class IEditableDateField(IEditableField, IRequireable):

    pass


class IEditableDateTimeField(IEditableField, IRequireable):

    pass


class IEditableIntegerChoice(IEditableChoice):

    value = zope.schema.Int(
        title=_(u'Stored Value'),
        )


class IEditableIntegerField(IEditableField, IRequireable):

    choices = zope.schema.List(
        title=_(u'Value Constraints'),
        description=_(
            u'If you want the field to be limited to a subset of possible values, '
            u'please enter them below. Leave blank otherwise.'),
        value_type=DictRow(schema=IEditableIntegerChoice),
        required=False,
        )


class IEditableDecimalChoice(IEditableChoice):

    value = zope.schema.Decimal(
        title=_(u'Stored Value'),
        )


class IEditableDecimalField(IEditableField, IRequireable):

    choices = zope.schema.List(
        title=_(u'Value Constraints'),
        description=_(
            u'If you want the field to be limited to a subset of possible values, '
            u'please enter them below. Leave blank otherwise.'),
        value_type=DictRow(schema=IEditableDecimalChoice),
        required=False,
        )


class IEditableStringChoice(IEditableChoice):

    value = zope.schema.TextLine(
        title=_(u'Stored Value'),
        )


class IEditableStringField(IEditableField, IRequireable, ICollectable):

    choices = zope.schema.List(
        title=_(u'Value Constraints'),
        description=_(
            u'If you want the field to be limited to a subset of possible values, '
            u'please enter them below. Leave blank otherwise.'),
        value_type=DictRow(schema=IEditableStringChoice),
        required=False,
        )


class IEditableTextField(IEditableField, IRequireable):

    pass


class IEditableObjectField(IEditableField):

    pass


typeInputSchemaMap = dict(
    boolean=IEditableBooleanField,
    date=IEditableDateField,
    datetime=IEditableDateTimeField,
    decimal=IEditableDecimalField,
    integer=IEditableIntegerField,
    string=IEditableStringField,
    text=IEditableTextField,
    object=IEditableObjectField,
    )


class IFormSummary(IOccamsFormComponent):
    """
    Form summary for listing purposes.
    """

    id = zope.schema.Int(
        title=_(u'Id'),
        description=_(u'Machine id'),
        readonly=True
        )

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

    field_count = zope.schema.Int(
        title=_(u'Fields'),
        description=_(
            u'Number of fields in the form, not including subform fields.'
            ),
        readonly=True,
        )
    revision = zope.schema.Int(
        title=_(u'Form Revision'),
        description=_(u'The revision of this form'),
        readonly=True,
        )

    state = zope.schema.TextLine(
        title=_(u'Form State'),
        description=_(u'The State of this form'),
        readonly=True,
        )

    # create_user = zope.schema.TextLine(
    #     title=_(u'Created By'),
    #     description=_(u'Person who created the form'),
    #     readonly=True,
    #     )

    create_date = zope.schema.Date(
        title=_(u'Create Date'),
        description=_(u'The date the form was created'),
        readonly=True,
        )

    publish_date = zope.schema.Date(
        title=_(u'Publish Date'),
        description=_(u'The date the form was published'),
        readonly=True,
        )

class IDataBaseItemContext(IOccamsFormComponent):
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


class IRepository(plone.directives.form.Schema):
    """
    Form repository entry point.
    Objects of this type offer services for managing forms as well as
    form EAV tables from ``occams.datastore.DataStore``
    """

    plone.directives.form.widget(session='z3c.form.browser.radio.RadioFieldWidget')
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



class ISessionUserFactory(zope.interface.Interface):
    """
    Set up a session that is friendly to our datastore
    """

