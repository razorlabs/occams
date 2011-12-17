import os.path
from datetime import datetime

from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.component import adapts
from zope.interface import Interface

from collective.z3cform.datagridfield import DataGridFieldFactory
from collective.beaker.interfaces import ISession
from plone.z3cform import layout
import z3c.form.form
import z3c.form.button
import z3c.form.field
import z3c.form.group
from  z3c.form.browser.text import TextFieldWidget
from z3c.form.interfaces import IAddForm

from avrc.data.store.interfaces import IDataStore

from occams.form import MessageFactory as _
from occams.form.interfaces import SESSION_KEY
from occams.form.interfaces import IEditableBooleanField
from occams.form.interfaces import IEditableDateField
from occams.form.interfaces import IEditableDateTimeField
from occams.form.interfaces import IEditableIntegerField
from occams.form.interfaces import IEditableDecimalField
from occams.form.interfaces import IEditableStringField
from occams.form.interfaces import IEditableTextField
from occams.form.interfaces import IEditableObjectField
from occams.form.interfaces import IEditableForm
from occams.form.interfaces import IDataBaseItemContext
from occams.form.interfaces import typesVocabulary
from occams.form.browser.widgets import fieldWidgetMap
from occams.form.browser.widgets import TextAreaFieldWidget
from occams.form.serialize import serializeForm
from occams.form.serialize import fieldFactory


editableFieldSchemaMap = dict(
    boolean=IEditableBooleanField,
    date=IEditableDateField,
    datetime=IEditableDateTimeField,
    decimal=IEditableDecimalField,
    integer=IEditableIntegerField,
    string=IEditableStringField,
    text=IEditableTextField,
    object=IEditableObjectField,
    )

class AddActions(z3c.form.button.ButtonActions):
    adapts(IAddForm, Interface, IDataBaseItemContext)

    def update(self):
        self.form.buttons = z3c.form.button.Buttons(
            z3c.form.button.Button('cancel', u'Cancel'),
            self.form.buttons,
            )
        super(AddActions, self).update()

class AddActionHandler(z3c.form.button.ButtonActionHandler):
    adapts(IAddForm, Interface, Interface, z3c.form.button.ButtonAction)

    def __call__(self):
        if self.action.name == 'form.buttons.cancel':
            self.form._finishedAdd = True
            return
        super(AddActionHandler, self).__call__()


class SchemaEditForm(z3c.form.form.EditForm):
    """
    Renders the form for editing, using a subform for the fields editor.
    """

    template = ViewPageTemplateFile('editor_templates/schema.pt')

    # Certain sub-form components (*cough* datagridfield) don't handle inline
    # validation very well, so we're turning it off on the entire edit for.
    ignoreRequest = True

    # The form's metadata properties (title, description, storage, etcc...)
    fields = z3c.form.field.Fields(IEditableForm).omit('name')

    # Override the tiny text area wiget with a nice bigger one
    fields['description'].widgetFactory = TextAreaFieldWidget

    # The form's entry fields (the ones the user enters data into when filling out)
    fieldsSubForm = None

    @property
    def prefix(self):
        return 'occams-form-master'

    def getContent(self):
        return ISession(self.request)[SESSION_KEY]

    def update(self):
        repository = self.context.getParentNode()
        formName = self.context.item.name
        formVersion = None

        # Load the form into the session, which is what we'll be using for
        # intermediary data storage while the form is being modified.
        browserSession = ISession(self.request)
        form = IDataStore(repository).schemata.get(formName, formVersion)
        browserSession[SESSION_KEY] = serializeForm(form)
        browserSession.save()

        # Render the fields editor form
        self.fieldsSubForm = FieldsForm(self.context, self.request)
        self.fieldsSubForm.update()
        super(SchemaEditForm, self).update()

    @z3c.form.button.buttonAndHandler(_('Cancel'), name='cancel')
    def handleCancel(self):
        """
        Cancels form changes.
        """
        # Delete the item in the session, leaving everything else intact
        browserSession = ISession(self.request)
        browserSession.delete()

    @z3c.form.button.buttonAndHandler(_(u'Complete'), name='complete')
    def handleComplete(self):
        """
        Save the form changes
        """
        # This is going to be huge
        return


class SchemaEditFormPloneView(layout.FormWrapper):
    """ 
    Form wrapper for Z3C so that it appears within Plone nicely
    """

    form = SchemaEditForm

    @property
    def label(self):
        return _(u'Edit: %s (%s)') % (self.context.item.title, self.context.item.name)

    def update(self):
        self.request.set('disable_border', True)
        super(SchemaEditFormPloneView, self).update()


class FieldsForm(z3c.form.group.GroupForm, z3c.form.form.Form):
    """
    Fields editor form.
    
    A note on sub-objects: There currently seems to be too many caveats
    surrounding object widgets (see ``z3c.form.object``). Given that, we
    will be using z3c group forms to represent sub objects.
    
    Uses Browser Session for data.
    """

    template = ViewPageTemplateFile('editor_templates/fields.pt')

    ignoreContext = True
    ignoreRequest = True

    # The form's fields, initialized in the constructor 
    groups = []

    def types(self):
        """
        Template helper for types
        """
        return typesVocabulary

    def update(self):
        groups = []
        objectFilter = lambda x: x['schema'] is not None
        orderSort = lambda i: i['order']

        formData = ISession(self.request)[SESSION_KEY]

        defaultFieldsetData = dict(interface=formData['name'], schema=formData)
        groups.append(Fieldset(defaultFieldsetData, self.request, self))

        fields = formData['fields']
        objects = sorted(filter(objectFilter, fields.values()), key=orderSort)

        for objectData in objects:
            groups.append(Fieldset(objectData, self.request, self))

        self.groups = groups
        super(FieldsForm, self).update()


class Fieldset(z3c.form.group.Group):
    """
    A generic group for fields of type Object to represent as a fieldset.
    This class can also be used for the top level form to be represented as a
    fieldset (has no referencing field).
    """

    @property
    def prefix(self):
        return self.context.get('name') or ''

    @property
    def label(self):
        return self.context.get('title')

    @property
    def description(self):
        return self.context.get('description')

    @property
    def parentUrl(self):
        return self.parentForm.context.getParentNode().absolute_url()

    def fieldContext(self, field=None):
        if field is None:
            fieldContext = self.context
        else:
            fieldContext = self.context['schema']['fields'][field.getName()]
        return fieldContext

    def url(self, field=None):
        # No field within the object specifiexd, process actual object field
        fieldContext = self.fieldContext(field)
        formName = fieldContext.get('interface') or ''
        fieldName = fieldContext.get('name') or ''
        return os.path.join(self.parentUrl, formName, fieldName)

    def editUrl(self, field=None):
        """
        Template helper for the edit URL of a field or group
        """
        return os.path.join(self.url(field), '@@edit')

    def deleteUrl(self, field=None):
        """
        Template helper for the delete URL of a field or group
        """
        return os.path.join(self.url(field), '@@delete')

    def type(self, field=None):
        """
        Template helper for retrieving the type of a field or group
        """
        return self.fieldContext(field).get('type')

    def version(self, field=None):
        """
        Template helper for retrieving the version of a field or group
        """
        versionRaw = self.fieldContext(field).get('version') or datetime.now()
        version = versionRaw.strftime('%Y-%m-%d')
        return version

    def update(self):
        fields = z3c.form.field.Fields()
        for fieldContext in sorted(self.context['schema']['fields'].values(), key=lambda x: x['order']):
            if fieldContext['type'] != 'object':
                schemaField = fieldFactory(fieldContext)
                fields += z3c.form.field.Fields(schemaField)
                widgetFactory = fieldWidgetMap.get(schemaField.__class__)
                if widgetFactory:
                    fields[schemaField.getName()].widgetFactory = widgetFactory
        self.fields = fields
        super(Fieldset, self).update()

    def updateWidgets(self):
        """
        Configure widgets, we'll mostly be disabling to prevent data entry.
        """
        super(Fieldset, self).updateWidgets()
        # Disable fields since we're not actually entering data
        for widget in self.widgets.values():
            widget.disabled = 'disabled'


class FieldPreview(z3c.form.form.Form):

    @property
    def label(self):
        return self.context.item.name

    def update(self):
        self.request.set('disable_border', True)
        schemaField = fieldFactory(self.context)
        self.fields = z3c.form.field.Fields(schemaField)
        widgetFactory = fieldWidgetMap.get(schemaField.__class__)
        if widgetFactory:
            self.fields[schemaField.getName()].widgetFactory = widgetFactory
        super(FieldPreview, self).update()

    def updateWidgets(self):
        super(FieldPreview, self).updateWidgets()
        for widget in self.widgets.values():
            widget.disabled = 'disabled'


class FieldFormMixin(object):

    typeName = None

    def datagridInitialise(self, subform, widget):
        widget.allow_reorder = True

        if self.typeName == 'boolean':
            subform.fields['value'].widgetFactory = TextFieldWidget
            widget.allow_insert = False
            widget.allow_delete = False
            widget.auto_append = False

    def datagridUpdateWidgets(self, subform, widgets, widget):
        if self.typeName == 'boolean':
            widgets['value'].readonly = 'readonly'

    def update(self):
        self.request.set('disable_border', True)
        self.fields = z3c.form.field.Fields(editableFieldSchemaMap[self.typeName])
        self.fields['description'].widgetFactory = TextAreaFieldWidget
        if 'choices' in self.fields:
            self.fields['choices'].widgetFactory = DataGridFieldFactory
        super(FieldFormMixin, self).update()


class BaseFieldAddForm(FieldFormMixin, z3c.form.form.AddForm):

    ignoreRequest = True

    @property
    def label(self):
        return _('New %s Field') % typesVocabulary.getTermByToken(self.typeName).title

    def nextURL(self):
        raise NotImplementedError

    def create(self, data):
        raise NotImplementedError

    def add(self, object):
        raise NotImplementedError


class BooleanFieldAddForm(BaseFieldAddForm):

    typeName = 'boolean'

    def updateWidgets(self):
        super(BooleanFieldAddForm, self).updateWidgets()
        self.widgets['choices'].value = [
            dict(title=u'False', value=False),
            dict(title=u'True', value=True),
            ]


class DateFieldAddForm(BaseFieldAddForm):

    typeName = 'date'


class DateTimeFieldAddForm(BaseFieldAddForm):

    typeName = 'datetime'


class DecimalFieldAddForm(BaseFieldAddForm):

    typeName = 'decimal'


class IntegerFieldAddForm(BaseFieldAddForm):

    typeName = 'integer'


class StringFieldAddForm(BaseFieldAddForm):

    typeName = 'string'


class TextFieldAddForm(BaseFieldAddForm):

    typeName = 'text'


class ObjectFieldAddForm(BaseFieldAddForm):

    typeName = 'object'


class FieldEditForm(FieldFormMixin, z3c.form.form.EditForm):

    ignoreRequest = True

    @property
    def label(self):
        return _(u'Edit: %s') % self.context.item.name

    def getContent(self):
        content = None
        browserSession = ISession(self.request)
        formData = browserSession[SESSION_KEY]
        formName = self.context.getParentNode().item.name
        fieldName = self.context.item.name
        if fieldName in formData['fields']:
            content = formData['fields'][fieldName]
        else:
            for name, fieldset in ['fields'].items():
                if fieldset['schema'] == formName:
                    content = fieldset['fields'][fieldName]
                    break
        return content

    def update(self):
        self.typeName = self.context.item.type
        super(FieldEditForm, self).update()

    def updateWidgets(self):
        super(FieldEditForm, self).updateWidgets()
        self.widgets['name'].readonly = 'readonly'

    @z3c.form.button.buttonAndHandler(_(u'Cancel'), name='cancel')
    def handleCancel(self, action):
        parent = self.context.getParentNode()
        self.request.response.redirect(os.path.join(parent.absolute_url(), '@@edit'))

    @z3c.form.button.buttonAndHandler(_('Apply'), name='apply')
    def handleApply(self, action):
        """
        Saves field changes to the browser session.
        """
        super(FieldEditForm, self).handleApply(action)
        if self.status == self.successMessage:
            self.request.response.redirect(os.path.join(self.context.absolute_url(), '@@view'))


class FieldOrder(z3c.form.form.Form):
    pass


class FieldRemove(z3c.form.form.Form):
    pass

