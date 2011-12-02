import os.path

from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.component import getUtility
from zope.interface import implements
import zope.schema

from plone.z3cform import layout
from plone.z3cform.crud import crud
import z3c.form.button
import z3c.form.field
import z3c.form.group

from collective.beaker.interfaces import ISession

from avrc.data.store.interfaces import IDataStore
from avrc.data.store import directives as datastore

from occams.form import MessageFactory as _
from occams.form.serialize import serializeForm
from occams.form.interfaces import SESSION_KEY
from occams.form.interfaces import IOccamsBrowserView
from occams.form.interfaces import IFormSummary
from occams.form.interfaces import IFormSummaryGenerator
from occams.form.interfaces import typesVocabulary
from occams.form.browser.widget import fieldWidgetMap


class ListingEditForm(crud.EditForm):
    """
    Custom form edit form.
    """
    label = None

    # No buttons for this release
    buttons = z3c.form.button.Buttons()


class SummaryListingForm(crud.CrudForm):
    """
    Lists the forms in the repository.
    No add form is needed as that will be a separate view.
    See ``configure.zcml`` for directive configuration.
    """

    addform_factory = crud.NullForm
    editform_factory = ListingEditForm

    # don't use changes count, apparently it's too confusing for users
    view_schema = z3c.form.field.Fields(IFormSummary).omit('name', 'changeCount')

    _items = None

    def get_items(self):
        """
        Return a listing of all the forms.
        """
        # Plone seems to call this method more than once, so make sure
        # we return an already generated listing.
        if self._items is None:
            datastore = IDataStore(self.context)
            generator = getUtility(IFormSummaryGenerator)
            listing = generator.getItems(datastore.session)
            self._items = [(summary.name, summary) for summary in listing]
        return self._items

    def link(self, item, field):
        """
        Renders a link to the form view
        """
        if field == 'title':
            # Redirect to the editor for now, until we can get some stats
            return os.path.join(self.context.absolute_url(), item.name, '@@edit')


class Listing(layout.FormWrapper):
    """
    Form wrapper so it can be rendered with a Plone layout and dynamic title.
    """
    implements(IOccamsBrowserView)

    form = SummaryListingForm

    @property
    def label(self):
        return self.context.title

    @property
    def description(self):
        return self.context.description


class DisabledFieldsMixin(object):

    def updateWidgets(self):
        """
        Configure widgets, we'll mostly be disabling to prevent data entry.
        """
        for field in self.fields.values():
            fieldType = field.field.__class__
            if fieldType in fieldWidgetMap:
                field.widgetFactory = fieldWidgetMap.get(fieldType)
        super(DisabledFieldsMixin, self).updateWidgets()
        # Disable fields since we're not actually entering data
        for widget in self.widgets.values():
            widget.disabled = 'disabled'


# We need a custom class for rendering disabled groups
class SchemaEditGroup(DisabledFieldsMixin, z3c.form.group.Group):

    _field = None


class SchemaEditForm(DisabledFieldsMixin, z3c.form.group.GroupForm, z3c.form.form.EditForm):
    """
    Displays a preview the form.
    
    A note on sub-objects: There currently seems to be too many caveats
    surrounding object widgets (see ``z3c.form.object``). Given that, we
    will be using z3c group forms to represent sub objects.
    """
    implements(IOccamsBrowserView)

    ignoreContext = True
    ignoreRequest = True

    enable_form_tabbing = False

    template = ViewPageTemplateFile('form_templates/edit.pt')

    fields = z3c.form.field.Fields()
    groups = ()

    def __init__(self, context, request):
        super(SchemaEditForm, self).__init__(context, request)
        self.request.set('disable_border', True)

        repository = self.context.getParentNode()
        formName = self.context.item.name
        formVersion = None
        form = IDataStore(repository).schemata.get(formName, formVersion)

        browserSession = ISession(self.request)
        browserSession.setdefault(SESSION_KEY, dict())
        browserSession[SESSION_KEY] = serializeForm(form)
        browserSession.save()

        groups = []
        defaultFieldNames = []

        # Update each field/group
        for name, field in zope.schema.getFieldsInOrder(form):
            # Put each sub-object form in a group
            if isinstance(field, zope.schema.Object):
                fieldset = SchemaEditGroup(None, self.request, self)
                fieldset.label = field.title
                fieldset.description = field.description
                fieldset.prefix = name
                fieldset._field = field
                fieldset.fields = z3c.form.field.Fields(field.schema)
                groups.append(fieldset)
            else:
                defaultFieldNames.append(name)

        self.fields = z3c.form.field.Fields(form).select(*defaultFieldNames)
        self.groups = groups

    @property
    def label(self):
        return self.context.item.title

    @property
    def description(self):
        return self.context.item.description

    @property
    def prefix(self):
        return str(self.context.item.name)

    def types(self):
        """
        Template helper for types
        """
        return typesVocabulary

    def _pathItems(self, item):
        if isinstance(item, z3c.form.group.Group):
            formName = item._field.schema.getName()
            fieldName = item.prefix
        else:
            formName = item.interface.getName()
            fieldName = item.__name__
        return (formName, fieldName)

    @property
    def parentUrl(self):
        return self.context.getParentNode().absolute_url()

    def editUrl(self, field):
        """
        Template helper for the edit URL of a field or group
        """
        (formName, fieldName) = self._pathItems(field)
        return os.path.join(self.parentUrl, formName, fieldName, '@@edit')

    def deleteUrl(self, field):
        """
        Template helper for the delete URL of a field or group
        """
        (formName, fieldName) = self._pathItems(field)
        return os.path.join(self.parentUrl, formName, fieldName, '@@delete')

    def fieldType(self, field):
        """
        Template helper for retrieving the type of a field or group
        """
        if isinstance(field, z3c.form.group.Group):
            type_ = 'object'
        else:
            type_ = datastore.type.bind().get(field)
            if type_ is None:
                type_ = typesVocabulary.getTerm(field.__class__).token
        return type_

    def fieldVersion(self, field):
        """
        Template helper for retrieving the version of a field or group
        """
        versionRaw = None
        if isinstance(field, z3c.form.group.Group):
            if field._field is not None:
                versionRaw = datastore.version.bind().get(field._field)
        else:
            versionRaw = datastore.version.bind().get(field)
        version = None
        if versionRaw is not None:
            version = versionRaw.strftime('%Y-%m-%d')
        return version

    @z3c.form.button.buttonAndHandler(_('Cancel'), name='cancel')
    def handleCancel(self):
        """
        Cancels form changes.
        """
        # Delete the item in the session, leaving everything else intact
        browserSession = ISession(self.request)
        del browserSession[self.context.item.name]
        browserSession.save()

    @z3c.form.button.buttonAndHandler(_(u'Complete'), name='complete')
    def handleComplete(self):
        """
        Save the form changes
        """
        # This is going to be huge
        return


class Edit(layout.FormWrapper):
    """ 
    Form wrapper for Z3C so that we can change the title.
    """

    form = SchemaEditForm

    def label(self):
        return u'Edit: %s (%s)' % (self.context.item.title, self.context.item.name)
