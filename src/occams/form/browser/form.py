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
from occams.form.interfaces import IEditableForm
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
    """
    Helper mixin for rendering custom disabled widgets. 
    Specify first in the inheritance list.
    """

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


class SchemaEditGroup(DisabledFieldsMixin, z3c.form.group.Group):
    """
    A generic group for fields that of type Object to represent as a fieldset.
    """

    fieldInParent = None

    @property
    def prefix(self):
        return str(self.context.getName())

    @property
    def label(self):
        return self.fieldInParent is not None and self.fieldInParent.title or None

    @property
    def description(self):
        return self.fieldInParent is not None and self.fieldInParent.description or None

    @property
    def parentUrl(self):
        return self.parentForm.context.getParentNode().absolute_url()

    def __init__(self, context, request, parentForm, fieldInParent=None):
        super(SchemaEditGroup, self).__init__(context, request, parentForm)
        self.fieldInParent = fieldInParent

        if self.fieldInParent is not None:
            fields = z3c.form.field.Fields(self.context)
        else:
            names = []
            for name, field in zope.schema.getFieldsInOrder(self.context):
                if not isinstance(field, zope.schema.Object):
                    names.append(name)
            fields = z3c.form.field.Fields(self.context).select(*names)

        # The fields NEED to be available before rendering otherwise the
        # widget overrides will not apply
        self.fields = fields

    def _pathItems(self, field):
        if field is None:
            formName = self.context.getName()
            fieldName = self.fieldInParent is not None and self.fieldInParent.__name__ or ''
        else:
            formName = field.interface.getName()
            fieldName = field.__name__
        return (formName, fieldName)

    def editUrl(self, field=None):
        """
        Template helper for the edit URL of a field or group
        """
        (formName, fieldName) = self._pathItems(field)
        return os.path.join(self.parentUrl, formName, fieldName, '@@edit')

    def deleteUrl(self, field=None):
        """
        Template helper for the delete URL of a field or group
        """
        (formName, fieldName) = self._pathItems(field)
        return os.path.join(self.parentUrl, formName, fieldName, '@@delete')

    def type(self, field=None):
        """
        Template helper for retrieving the type of a field or group
        """
        if field is None:
            type_ = 'object'
        else:
            type_ = datastore.type.bind().get(field)
            if type_ is None:
                type_ = typesVocabulary.getTerm(field.__class__).token
        return type_

    def version(self, field=None):
        """
        Template helper for retrieving the version of a field or group
        """
        version = None
        if field is None:
            if self.fieldInParent is not None:
                versionRaw = datastore.version.bind().get(self.fieldInParent)
            else:
                versionRaw = None
        else:
            versionRaw = datastore.version.bind().get(field)
        if versionRaw is not None:
            version = versionRaw.strftime('%Y-%m-%d')
        return version


class SchemaEditForm(z3c.form.group.GroupForm, z3c.form.form.EditForm):
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

    # The form's metadata properties
    fields = z3c.form.field.Fields(IEditableForm).omit('name')

    # The form's fields, initialized in the constructor 
    groups = ()

    @property
    def prefix(self):
        return 'occams-form-master'

    def __init__(self, context, request):
        super(SchemaEditForm, self).__init__(context, request)
        self.request.set('disable_border', True)

    def getContent(self):
        return ISession(self.request)[SESSION_KEY]

    def types(self):
        """
        Template helper for types
        """
        return typesVocabulary

    def updateWidgets(self):
        repository = self.context.getParentNode()
        formName = self.context.item.name
        formVersion = None

        # TODO: It might be useful to load the form else where and simply
        # use the session data to render the current progress. The reason
        # this might be necessary is because in the future the form
        # might be loaded from a "Change Request" queue and not from DS
        # directly.
        form = IDataStore(repository).schemata.get(formName, formVersion)
        browserSession = ISession(self.request)
        browserSession.setdefault(SESSION_KEY, dict())
        browserSession[SESSION_KEY] = serializeForm(form)
        browserSession.save()

        groups = [SchemaEditGroup(form, self.request, self, None)]

        # Update each field/group
        for name, field in zope.schema.getFieldsInOrder(form):
            # Put each sub-object form in a group
            if isinstance(field, zope.schema.Object):
                groups.append(SchemaEditGroup(field.schema, self.request, self, field))

        self.groups = groups
        super(SchemaEditForm, self).updateWidgets()

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

