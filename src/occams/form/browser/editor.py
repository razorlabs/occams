import os.path
from datetime import datetime

from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.interface import implements
import zope.schema

from collective.z3cform.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield import DictRow
from collective.beaker.interfaces import ISession
from plone.z3cform import layout
import z3c.form.form
import z3c.form.button
import z3c.form.field
import z3c.form.group

from avrc.data.store.interfaces import IDataStore
from avrc.data.store import directives as datastore

from occams.form import MessageFactory as _
from occams.form.interfaces import SESSION_KEY
from occams.form.interfaces import IOccamsBrowserView
from occams.form.interfaces import IEditableField
from occams.form.interfaces import IEditableForm
from occams.form.interfaces import IEditableStringChoice
from occams.form.interfaces import typesVocabulary
from occams.form.browser.widgets import fieldWidgetMap
from occams.form.browser.widgets import TextAreaFieldWidget
from occams.form.serialize import serializeForm
from occams.form.serialize import fieldFactory


class Editor(layout.FormWrapper):
    """ 
    Form wrapper for Z3C so that we can change the title.
    """

    @property
    def form(self):
        return SchemaEditForm

    @property
    def label(self):
        return u'Edit: %s (%s)' % (self.context.item.title, self.context.item.name)

    def __init__(self, context, request):
        super(Editor, self).__init__(context, request)
        self.request.set('disable_border', True)


class SchemaEditForm(z3c.form.form.EditForm):
    """
    Renders the form for editing, using a subform for the fields editor.
    """

    implements(IOccamsBrowserView)

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
        form = IDataStore(repository).schemata.get(formName, formVersion)
        browserSession = ISession(self.request)
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
        del browserSession[SESSION_KEY]
        browserSession.save()

    @z3c.form.button.buttonAndHandler(_(u'Complete'), name='complete')
    def handleComplete(self):
        """
        Save the form changes
        """
        # This is going to be huge
        return


class FieldsForm(z3c.form.group.GroupForm, z3c.form.form.Form):
    """
    Fields editor form.
    
    A note on sub-objects: There currently seems to be too many caveats
    surrounding object widgets (see ``z3c.form.object``). Given that, we
    will be using z3c group forms to represent sub objects.
    
    Uses Browser Session for data.
    """

    implements(IOccamsBrowserView)

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
        objectFilter = lambda x: x['schema'] is not None
        orderSort = lambda i: i['order']

        formData = ISession(self.request)[SESSION_KEY]

        defaultFieldsetData = dict(interface=formData['name'], schema=formData)
        self.groups.append(Fieldset(defaultFieldsetData, self.request, self))

        fields = formData['fields']
        objects = sorted(filter(objectFilter, fields.values()), key=orderSort)

        for objectData in objects:
            self.groups.append(Fieldset(objectData, self.request, self))

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
    implements(IOccamsBrowserView)

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


#        choicesWidget.allow_insert = True  # Enable/Disable the insert button on the right 
#        choicesWidget.allow_delete = True  # Enable/Disable the delete button on the right 
#        choicesWidget.auto_append = False   # Enable/Disable the auto-append feature 

class BaseFieldAdd(z3c.form.form.AddForm):
    implements(IOccamsBrowserView)

    ignoreRequest = True

    fields = z3c.form.field.Fields(IEditableField) + \
        z3c.form.field.Fields(
            zope.schema.List(
                __name__='choices',
                title=_(u'Value Choices'),
                description=_(
                    u'If you want the field to be have value constraints, '
                    u'please enter them below. Leave blank otherwise.'),
                value_type=DictRow(schema=IEditableStringChoice),
                required=False,
                )
            )

    fields['description'].widgetFactory = TextAreaFieldWidget
    fields['choices'].widgetFactory = DataGridFieldFactory

    type_ = None

    @property
    def label(self):
        return _(u'New %s Field') % typesVocabulary.getTermByToken(self.type_).title

    def update(self):
        self.request.set('disable_border', True)
        super(BaseFieldAdd, self).update()

    def updateWidgets(self):
        super(BaseFieldAdd, self).updateWidgets()
        self.widgets['choices'].allow_reorder = True


class FieldAddBoolean(BaseFieldAdd):
    type_ = 'boolean'


class FieldAddInteger(BaseFieldAdd):
    type_ = 'integer'


class FieldAddDecimal(BaseFieldAdd):
    type_ = 'decimal'


class FieldAddString(BaseFieldAdd):
    type_ = 'string'


class FieldAddText(BaseFieldAdd):
    type_ = 'text'


class FieldAddDateTime(BaseFieldAdd):
    type_ = 'datetime'


class FieldAddTime(BaseFieldAdd):
    type_ = 'time'


class FieldAddObject(BaseFieldAdd):
    type_ = 'object'


class FieldEdit(z3c.form.form.EditForm):
    implements(IOccamsBrowserView)

    ignoreRequest = True

    # Render the name as input (readonly by default renders as VIEW)
    fields = z3c.form.field.Fields(IEditableField).omit('name') + \
        z3c.form.field.Fields(
            zope.schema.List(
                __name__='choices',
                title=_(u'Value Choices'),
                description=_(
                    u'If you want the field to be have value constraints, '
                    u'please enter them below. Leave blank otherwise.'),
                value_type=DictRow(schema=IEditableStringChoice),
                required=False,
                )
            )

    fields['description'].widgetFactory = TextAreaFieldWidget
    fields['choices'].widgetFactory = DataGridFieldFactory

    @property
    def label(self):
        return 'Edit: %s' % self.context.item.name

    def getContent(self):
        content = None
        formName = self.context.getParentNode().item.name
        fieldName = self.context.item.name
        for name, group in ISession(self.request)[SESSION_KEY]['groups'].items():
            if group['schema'] == formName:
                content = group['fields'][fieldName]
                break
        return content

    def update(self):
        self.request.set('disable_border', True)
        super(FieldEdit, self).update()

    @z3c.form.button.buttonAndHandler(_(u'Cancel'), name='cancel')
    def handleCancel(self, action):
        parent = self.context.getParentNode()
        self.request.response.redirect(os.path.join(parent.absolute_url(), '@@edit'))

    @z3c.form.button.buttonAndHandler(_('Apply'), name='apply')
    def handleApply(self, action):
        """
        Saves field changes to the browser session.
        """
        super(FieldEdit, self).handleApply(action)
        if self.status == self.successMessage:
            self.request.response.redirect(os.path.join(self.context.absolute_url(), '@@view'))


class FieldOrder(object):
    pass


class FieldRemove(object):
    pass
