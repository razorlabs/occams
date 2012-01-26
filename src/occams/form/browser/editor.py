from copy import copy
from datetime import datetime
from decimal import Decimal
import json
import os.path

from collective.z3cform.datagridfield import DataGridFieldFactory
from collective.beaker.interfaces import ISession
from plone.z3cform import layout
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.publisher.browser import BrowserView
import zope.schema
from zExceptions import NotFound
import z3c.form.form
import z3c.form.button
import z3c.form.field
import z3c.form.group
from z3c.form.interfaces import HIDDEN_MODE
from z3c.form.interfaces import INPUT_MODE
from  z3c.form.browser.text import TextFieldWidget

from avrc.data.store.interfaces import IDataStore
from occams.form import MessageFactory as _
from occams.form.interfaces import DATA_KEY
from occams.form.interfaces import IAttributeContext
from occams.form.interfaces import IEditableForm
from occams.form.interfaces import IEditableField
from occams.form.interfaces import typeInputSchemaMap
from occams.form.interfaces import typesVocabulary
from occams.form.browser.widgets import fieldWidgetMap
from occams.form.browser.widgets import TextAreaFieldWidget
from occams.form.serialize import serializeForm
from occams.form.serialize import fieldFactory
from occams.form.serialize import cleanupChoices
from occams.form.serialize import moveField


class FormEditForm(z3c.form.form.EditForm):
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

    @property
    def prefix(self):
        return self.context.__name__

    def getContent(self):
        return self.context.data

    def update(self):
        """
        Loads form metadata into browser session
        """
        self.request.set('disable_border', True)

        formName = self.context.__name__
        formVersion = None
        browserSession = ISession(self.request)
        browserSession.setdefault(DATA_KEY, {})
        workspace = browserSession[DATA_KEY]

        if formName not in workspace:
            repository = self.context.getParentNode()
            form = IDataStore(repository).schemata.get(formName, formVersion)
            formData = serializeForm(form)
            workspace[formName] = formData
            self.context.data = formData
            browserSession.save()

        # Render the fields editor form
        self.fieldsSubForm = FieldsetsForm(self.context, self.request)
        self.fieldsSubForm.update()

        # Continue the z3c form process
        super(FormEditForm, self).update()

    @z3c.form.button.buttonAndHandler(_('Cancel'), name='cancel')
    def handleCancel(self):
        """
        Cancels form changes.
        """
        del ISession(self.request)[DATA_KEY][self.context.__name__]

    @z3c.form.button.buttonAndHandler(_(u'Complete'), name='submit')
    def handleComplete(self):
        """
        Save the form changes
        """
        # This is going to be huge
        return


class FormEditFormPloneView(layout.FormWrapper):
    """
    Form wrapper for Z3C so that it appears within Plone nicely
    """

    form = FormEditForm

    @property
    def label(self):
        return _(u'Edit: %s (%s)') % (self.context.title, self.context.__name__)


class FieldsetsForm(z3c.form.group.GroupForm, z3c.form.form.Form):
    """
    Fields editor form.

    A note on sub-objects: There currently seems to be too many caveats
    surrounding object widgets (see ``z3c.form.object``). Given that, we
    will be using z3c group forms to represent sub objects.

    Uses Browser Session for data.
    """

    template = ViewPageTemplateFile('editor_templates/fields.pt')

    # This we're rendering disabled fields, we don't need context data or kss
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
        """
        Configures fields based on session data
        """
        self.request.set('disable_border', True)
        groups = []
        objectFilter = lambda x: bool(x['schema'])
        orderSort = lambda i: i['order']

        formData = self.context.data

        defaultFieldsetData = dict(interface=formData['name'], schema=formData)
        groups.append(Fieldset(defaultFieldsetData, self.request, self))

        fields = formData['fields']
        objects = sorted(filter(objectFilter, fields.values()), key=orderSort)

        for objectData in objects:
            groups.append(Fieldset(objectData, self.request, self))

        self.groups = groups
        super(FieldsetsForm, self).update()


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

    def fieldData(self, field=None):
        """
        Returns either the data of the fieldset or the specified field
        """
        if field is None:
            data = self.context
        else:
            data = self.context['schema']['fields'][field.getName()]
        return data

    def url(self, field=None):
        # No field within the object specified, process actual object field
        parentUrl = self.parentForm.context.absolute_url()
        parts = [parentUrl]
        if self.prefix:
            parts.append(self.prefix)
        if field:
            fieldData = self.fieldData(field)
            parts.append(fieldData.get('name'))
        return os.path.join(*parts)

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
        return self.fieldData(field).get('type')

    def version(self, field=None):
        """
        Template helper for retrieving the version of a field or group
        """
        versionRaw = self.fieldData(field).get('version') or datetime.now()
        return versionRaw.strftime('%Y-%m-%d')

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
    """
    Preview of form fields for re-rendering single fields during form editing
    """

    ignoreRequest = True

    @property
    def label(self):
        return 'Preview: %s' % self.context.item.name

    def getContent(self):
        return self.context.data

    def update(self):
        self.request.set('disable_border', True)
        schemaField = fieldFactory(self.getContent())
        self.fields = z3c.form.field.Fields(schemaField)
        widgetFactory = fieldWidgetMap.get(schemaField.__class__)
        if widgetFactory:
            self.fields[schemaField.getName()].widgetFactory = widgetFactory
        super(FieldPreview, self).update()

    def updateWidgets(self):
        """
        Disables widgets since we're not really entering data
        """
        super(FieldPreview, self).updateWidgets()
        for widget in self.widgets.values():
            widget.disabled = 'disabled'


class FieldJsonView(BrowserView):
    """
    JSON view for form fields
    """

    def __call__(self):
        """
        Returns a clean copy of the current state of the field.
        Additionally adds an extra ``view`` field in the JSON object
        for rendering the field on the client side
        """
        self.request.set('disable_border', True)
        data = copy(self.context.data)
        if data['schema']:
            del data['schema']
        # For client-side ajax update of the field
        if data['type'] != 'object':
            data['view'] = FieldPreview(self.context, self.request)()
        else:
            data['view'] = None
        # JSON doesn't understand dates, gotta clean that up too
        data['version'] = data['version'].date().isoformat()
        # Cleanup choice values (in case they're decimals)
        if data['choices']:
            for choice in data['choices']:
                if isinstance(choice['value'], Decimal):
                    choice['value'] = str(choice['value'])
        return json.dumps(data)


class FieldDeleteForm(z3c.form.form.Form):
    """
    Delete confirmation form for fields.
    """

    template = ViewPageTemplateFile('editor_templates/delete.pt')

    @property
    def label(self):
        return _(u'Delete: %s') % self.context.__name__

    def getContent(self):
        return self.context.data

    def update(self):
        self.request.set('disable_border', True)
        super(FieldDeleteForm, self).udpate()

    @z3c.form.button.buttonAndHandler(_(u'Cancel'), name='cancel')
    def handleCancel(self, action):
        self.request.response.setStatus(304);

    @z3c.form.button.buttonAndHandler(_(u'Yes, I\'m sure'), name='delete')
    def handleDelete(self, action):
        del  self.context.data['fields'][self.context.__name__]
        self.request.response.setStatus(200);


class FieldOrderForm(z3c.form.form.Form):
    """
    Form for editing the position of a field in a form.
    """

    @property
    def label(self):
        return _(u'Reorder: %s') % self.context.__name__

    def getContent(self):
        return self.context.data

    def update(self):
        self.request.set('disable_border', True)

        objectFilter = lambda x: bool(x['schema'])
        orderSort = lambda i: i['order']
        fields = ISession(self.request)[DATA_KEY]['fields']
        objects = sorted(filter(objectFilter, fields.values()), key=orderSort)

        self.fields = z3c.form.field.Fields(zope.schema.Choice(
            __name__='sender',
            title=_(u'Sender Fieldset'),
            values=[o['name'] for o in objects],
            required=False,
            ))
        self.fields += z3c.form.field.Fields(IEditableField).select('order')

        super(FieldOrderForm, self).update()

    def applyChanges(self, data):
        changes = dict()
        position = data['order']
        moved = moveField(self.getContent(), self.context.__name__, position)
        if moved:
            changes[self.fields['order'].interface] = moved
            self.request.response.setStatus(200)
        else:
            self.request.response.setStatus(304)
        return changes


class FieldFormInputHelper(object):
    """
    Helper class for displaying the inputs for editing field metadata.
    """

    def getType(self):
        """
        Sub classes must return the value type they are editing
        """
        raise NotImplementedError

    def getMetadataFields(self):
        """
        Configures fields based on type
        """
        if not hasattr(self, '_fields'):
            type_ = self.getType()
            schema = typeInputSchemaMap[type_]
            fields = z3c.form.field.Fields(schema)
            fields['description'].widgetFactory = TextAreaFieldWidget
            if 'choices' in fields:
                fields['choices'].widgetFactory = DataGridFieldFactory
            self._fields = fields
        return self._fields

    def datagridInitialise(self, subform, widget):
        """
        Callback for configuring grid widgets
        """
        widget.allow_reorder = True
        widget.auto_append = True

        # Booleans are not allowed to have more than two values (duh)
        if self.getType() == 'boolean':
            subform.fields['value'].widgetFactory = TextFieldWidget
            widget.allow_insert = False
            widget.allow_delete = False
        else:
            widget.allow_insert = True
            widget.allow_delete = True

    def datagridUpdateWidgets(self, subform, widgets, widget):
        """
        Callback for updating grid widgets
        """
        # Booleans are special in that their values are known
        if self.getType() == 'boolean':
            widgets['value'].readonly = 'readonly'


class FieldAddForm(FieldFormInputHelper, z3c.form.form.AddForm):
    """
    Add form for fields.

    Optionally takes a request variable ``order`` to preset where the
    field will be added (otherwise at the end of the form)
    """
    z3c.form.form.extends(z3c.form.form.AddForm)

    @property
    def label(self):
        return _('New %s Field') % typesVocabulary.getTermByToken(self.typeName).title

    @property
    def fields(self):
        return self.getMetadataFields()

    def getType(self):
        return self.__name__.split('-').pop()

    def update(self):
        self.request.set('disable_border', True)
        if IAttributeContext.providedBy(self.context) and \
            self.context['type'] != 'object':
            raise NotFound()
        self.buttons = self.buttons.select('cancel', 'add')
        if 'order' in self.request:
            self.fields['order'].mode = HIDDEN_MODE
        else:
            self.fields['order'].mode = INPUT_MODE
        super(FieldAddForm, self).update()

    def updateWidgets(self):
        super(FieldAddForm, self).updateWidgets()
        self.widgets['order'].value = self.request.get('order')
        if self.getType() == 'boolean':
            self.widgets['choices'].value = [
                dict(title=u'False', value=False),
                dict(title=u'True', value=True),
                ]

    def create(self, data):
        if IAttributeContext.providedBy(self.context):
            formData = self.context.data['schema']
        else:
            formData = self.context.data

        cleanupChoices(data)
        position = data['order']

        fieldCount = len(formData['fields'])
        schema = None

        if position is None or position > fieldCount:
            position = fieldCount
        elif position is None or position < 0:
            position = 0

        if self.getType() == 'object':
            schema = dict(
                name=data['schemaName'],
                title=data['title'],
                description='auto-generated class',
                version=datetime.now(),
                fields=dict(),
                )

            del data['schemaName']

        data.update(dict(
            version=datetime.now(),
            type=self.getType(),
            interface=formData['name'],
            is_collection=data.get('is_collection', False),
            schema=schema,
            order=position,
            ))

        return data

    def add(self, item):
        if IAttributeContext.providedBy(self.context):
            formData = self.context.data['schema']
        else:
            formData = self.context.data
        formData['fields'][item['name']] = item
        moveField(formData, item['name'], item['order'])
        self._newItem = item

    def nextURL(self):
        url = self.context.absolute_url()
        if self._newItem is not None:
            url = os.path.join(url, self._newItem['name'], '@@json')
        return url

    @z3c.form.button.buttonAndHandler(_(u'Cancel'), name='cancel')
    def handleCancel(self, action):
        self._finishedAdd = True


class FieldEditForm(FieldFormInputHelper, z3c.form.form.EditForm):
    """
    Edit form for field.
    """
    z3c.form.form.extends(z3c.form.form.EditForm)

    @property
    def label(self):
        return _(u'Edit: %s') % self.context.__name__

    @property
    def fields(self):
        return self.getMetadataFields()

    def getType(self):
        return self.context['type']

    def getContent(self):
        return self.context.data

    def update(self):
        self.request.set('disable_border', True)
        self.buttons = self.buttons.select('cancel', 'apply')
        self.fields['order'].mode = HIDDEN_MODE
        super(FieldEditForm, self).update()

    def updateWidgets(self):
        super(FieldEditForm, self).updateWidgets()
        self.widgets['name'].readonly = 'readonly'

    @z3c.form.button.buttonAndHandler(_(u'Cancel'), name='cancel')
    def handleCancel(self, action):
        parent = self.context.getParentNode()
        nextUrl = os.path.join(parent.absolute_url())
        self.request.response.redirect(nextUrl)

    def applyChanges(self, data):
        """
        Commits changes to the browser session data
        """
        cleanupChoices(data)
        # Now do the default changes
        changes = super(FieldEditForm, self).applyChanges(data);
        if changes:
            self.getContent()['version'] = datetime.now()
        nextUrl = os.path.join(self.context.absolute_url(), '@@json')
        self.request.response.redirect(nextUrl)
        return changes
