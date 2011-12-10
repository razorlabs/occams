import os.path

from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.interface import implements
import zope.schema
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.vocabulary import SimpleTerm

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
        progress = ISession(self.request)[SESSION_KEY]

        fieldFilter = lambda x: x['schema'] is None
        fieldsetFilter = lambda x: x['schema'] is not None
        orderSort = lambda i: i['order']

        fields = sorted(filter(fieldFilter, progress.values()), orderSort)
        objects = sorted(filter(fieldsetFilter, progress.values()), orderSort)

        self.groups.append(Fieldset(dict(name=None, fields=fields)), self.request, self)

        for object_ in objects:
            self.groups.append(Fieldset(object_, self.request, self))

        super(FieldsForm, self).update()


class Fieldset(z3c.form.group.Group):
    """
    A generic group for fields that of type Object to represent as a fieldset.
    """

    @property
    def prefix(self):
        return self.context.get('name')

    @property
    def label(self):
        return self.context.get('title')

    @property
    def description(self):
        return self.context.get('description')

    @property
    def parentUrl(self):
        return self.parentForm.context.getParentNode().absolute_url()

    def __init__(self, context, request, parentForm):
        super(Fieldset, self).__init__(context, request, parentForm)

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

    def updateWidgets(self):
        """
        Configure widgets, we'll mostly be disabling to prevent data entry.
        """
        for field in self.fields.values():
            fieldType = field.field.__class__
            if fieldType in fieldWidgetMap:
                field.widgetFactory = fieldWidgetMap.get(fieldType)
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
        super(FieldPreview, self).update()

    def updateWidgets(self):
        field = self.getContent()
        factory = typesVocabulary.getTermByToken(field['type']).value
        options = dict()

        if field['choices']:
            terms = []
            validator = factory(**options)
            for choice in sorted(field['choices'].values(), key=lambda c: c['order']):
                (token, title, value) = (choice['name'], choice['title'], choice['value'])
                value = validator.fromUnicode(value)
                term = SimpleTerm(token=str(token), title=title, value=value)
                terms.append(term)
            factory = zope.schema.Choice
            options = dict(vocabulary=SimpleVocabulary(terms))

        if field['is_collection']:
            # Wrap the factory and options into the list
            options = dict(value_type=factory(**options), unique=True)
            factory = zope.schema.List

        if field['default']:
            options['default'] = factory(**options).fromUnicode(field['default'])

        # Update the options with the final field parameters
        options.update(dict(
            __name__=str(field['name']),
            title=field['title'],
            description=field['description'],
            readonly=field['is_readonly'],
            required=field['is_required'],
            ))

        result = factory(**options)
        result.order = field['order']

        self.fields = z3c.form.field.Fields(result)

        for field in self.fields.values():
            fieldType = field.field.__class__
            if fieldType in fieldWidgetMap:
                field.widgetFactory = fieldWidgetMap.get(fieldType)

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
