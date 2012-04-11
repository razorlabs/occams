from decimal import Decimal
import json
import os.path
from copy import copy

from collective.z3cform.datagridfield import DataGridField
from collective.z3cform.datagridfield import DataGridFieldFactory
import plone.z3cform.layout
from Products.statusmessages.interfaces import IStatusMessage
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.publisher.browser import BrowserView
import zope.interface
import zope.schema
from zExceptions import NotFound
import z3c.form.form
import z3c.form.button
import z3c.form.field
import z3c.form.group
from z3c.form.interfaces import HIDDEN_MODE
from  z3c.form.browser.text import TextFieldWidget
import z3c.form.validator
from sqlalchemy.orm.session import Session as sqlalchemysession
from z3c.saconfig import named_scoped_session
import datetime
from zope.security import checkPermission
from AccessControl import getSecurityManager

from occams.form import MessageFactory as _
from occams.form.form import StandardWidgetsMixin
from occams.form.form import TextAreaFieldWidget
from occams.form.interfaces import IAttributeContext
from occams.form.interfaces import IEditableForm
from occams.form.interfaces import IEditableField
from occams.form.interfaces import IRepository
from occams.form.interfaces import ISchemaContext
from occams.form.interfaces import typeInputSchemaMap
from occams.form.interfaces import typesVocabulary
from occams.form.traversal import closest
from occams.form.serialize import listFieldsets
from occams.form.serialize import fieldFactory
from occams.form.serialize import cleanupChoices
from occams.form.serialize import reservedWords
from occams.form.serialize import camelize
from occams.form.serialize import symbolize
from occams.form.browser.preview import DisabledMixin
from occams.form.form import UserAwareMixin


# Helper Methods
def applyChoiceChanges(field, choiceData):
    # Need a helper to add choice changes
    if field.choices:
        def findChoice(value, itemlist):
            for i, item in enumerate(itemlist):
                if item['value'] == value:
                    return itemlist.pop(i)
            return None

        subSession = sqlalchemysession.object_session(field)
        for choice in field.choices:
            choice.order = choice.order+100
        subSession.flush()

        for choice in field.choices:
            newValue = findChoice(choice.value, choiceData)
            if newValue is not None:
                for key, value in newValue.items():
                    setattr(choice, key, value)
            else:
                field.choices.remove(choice)

    for new_choice in choiceData:
        newChoice = model.Choice(
            name = str(new_choice['name']),
            title = unicode(new_choice['title']),
            order = new_choice['order'],
            value = unicode(new_choice['value'])
            )
        field.choices.append(newChoice)
    return field

def moveField(form, field, after=None):
    subSession = sqlalchemysession.object_session(form)
    if after is None:
        field.order = 100
    else:
        field.order = form[after].order + 101
    # Move everything that follows
    for formfield in sorted(form.values(), key=lambda i: i.order):
        formfield.order += 100
        if formfield != field and formfield.order >= field.order:
            formfield.order += 1
    subSession.flush()
    ## ok, we need to reorder everything
    for order, formfield in enumerate(sorted(form.values(), key=lambda i: i.order)):
        formfield.order = order
    return form


class FormEditForm(StandardWidgetsMixin, UserAwareMixin, z3c.form.form.EditForm):
    """
    Renders the form for editing, using a subform for the fields editor.
    """

    template = ViewPageTemplateFile('editor_templates/schema_edit.pt')

    # Certain sub-form components (*cough* datagridfield) don't handle inline
    # validation very well, so we're turning it off on the entire edit for.
    ignoreRequest = True

    # The form's metadata properties (title, description, storage, etcc...)
    fields = z3c.form.field.Fields(IEditableForm).omit('name')

    cancelMessage = _(u'Changes canceled, nothing saved.')

    @property
    def label(self):
        formlabel = 'Edit: ' + self.context.item.title 
        formlabel = formlabel + ' -- Draft created by %(user_name)s on %(create_date)s' % dict(
                user_name=str(self.context.item.create_user.key),
                create_date=self.context.item.create_date.strftime('%Y/%m/%d'))
        return _(u'%s') % (formlabel)

    def getContent(self):
        return self.context.data

    def update(self):
        """
        Loads form metadata into browser session
        """
        self.request.set('disable_border', True)
        self.request.set('disable_plone.rightcolumn', True)
        self.request.set('disable_plone.leftcolumn', True)
        # Render the fields editor form
        self.fieldsSubForm = FieldsetsForm(self.context, self.request)
        self.fieldsSubForm.update()

        # Continue the z3c form process
        super(FormEditForm, self).update()

    @z3c.form.button.buttonAndHandler(_(u'<< Back to Listing'), name='cancel')
    def handleCancel(self, action):
        repository = closest(self.context, IRepository)
        self.request.response.redirect(repository.absolute_url())


    def can_discard(self):
        return not self.context.item.publish_date and \
            (self.context.item.create_user.key == getSecurityManager().getUser().getId() or \
                checkPermission("occams.form.RemoveForm", self.context)
            )

    @z3c.form.button.buttonAndHandler(_(u'Discard Draft'), name='discard', condition=lambda self: self.can_discard())
    def handleDiscard(self, action):
        """
        Discard form changes.
        """
        Session = named_scoped_session(self.context.session)
        Session.delete(self.context.item)
        Session.flush()
        repository = closest(self.context, IRepository)

        self.request.response.redirect(repository.absolute_url())
        IStatusMessage(self.request).add(self.cancelMessage)

    def can_submit(self):
        return (self.context.item.state == 'draft')

    @z3c.form.button.buttonAndHandler(_(u'Submit Draft for Review'), name='submit', condition=lambda self: self.can_submit())
    def handleSubmit(self, action):
        """
        Save the form changes
        """
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
        else:
            Session = named_scoped_session(self.context.session)
            self.context.item.title = unicode(data['title'])
            if data['description']:
                self.context.item.description = unicode(data['description'])
            self.context.item.state = 'review'
            Session.flush()
            repository = closest(self.context, IRepository)
            self.request.response.redirect(repository.absolute_url())
            IStatusMessage(self.request).add(self.successMessage)

    def can_publish(self):
        return checkPermission("occams.form.PublishForm", self.context)  and \
                  not self.context.item.publish_date
        

    @z3c.form.button.buttonAndHandler(_(u'Publish Draft'), name='publish')
    def handleComplete(self, action):
        """
        Save the form changes
        """
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
        else:
            Session = named_scoped_session(self.context.session)
            self.context.item.title = unicode(data['title'])
            if data['description']:
                self.context.item.description = unicode(data['description'])
            self.context.item.state = 'published'
            if data['publish_date']:
                self.context.item.publish_date = data['publish_date']
            else:
                self.context.item.publish_date = datetime.date.today()
            Session.flush()
            repository = closest(self.context, IRepository)
            self.request.response.redirect(repository.absolute_url())
            IStatusMessage(self.request).add(self.successMessage)


# Need to customize the template further, use wrapper
FormEditFormView = plone.z3cform.layout.wrap_form(FormEditForm)


class FieldsetsForm(z3c.form.group.GroupForm, z3c.form.form.Form):
    """
    Fields editor form.

    A note on sub-objects: There currently seems to be too many caveats
    surrounding object widgets (see ``z3c.form.object``). Given that, we
    will be using z3c group forms to represent sub objects.

    Uses Browser Session for data.
    """

    template = ViewPageTemplateFile('editor_templates/schema_fields.pt')

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


class Fieldset(StandardWidgetsMixin, DisabledMixin, z3c.form.group.Group):
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
            data = self.context['schema']['fields'][field.__name__]
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

    def update(self):
        fields = z3c.form.field.Fields()
        serializedFields = self.context['schema']['fields'].values()
        for fieldContext in sorted(serializedFields, key=lambda x: x['order']):
            if fieldContext['type'] != 'object':
                schemaField = fieldFactory(fieldContext)
                fields += z3c.form.field.Fields(schemaField)
        self.fields = fields
        super(Fieldset, self).update()

class FieldPreview(StandardWidgetsMixin, DisabledMixin, z3c.form.form.Form):
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
        super(FieldPreview, self).update()


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
        data = copy(self.context.data)
        if data['schema']:
            del data['schema']
        # For client-side ajax update of the field
        if data['type'] != 'object':
            data['view'] = FieldPreview(self.context, self.request)()
        else:
            data['view'] = None
        # JSON doesn't understand dates, gotta clean that up too
        # Cleanup choice values (in case they're decimals)
        if data['choices']:
            for choice in data['choices']:
                if isinstance(choice['value'], Decimal):
                    choice['value'] = str(choice['value'])
        return json.dumps(data)


class FieldDeleteForm(StandardWidgetsMixin, z3c.form.form.Form):
    """
    Delete confirmation form for fields.
    """

    template = ViewPageTemplateFile('editor_templates/field_delete.pt')

    prefix = 'delete'

    @property
    def label(self):
        return _(u'Delete: %s') % self.context.__name__

    def getContent(self):
        return self.context.data

    def update(self):
        self.request.set('disable_border', True)
        super(FieldDeleteForm, self).update()

    @z3c.form.button.buttonAndHandler(_(u'Cancel'), name='cancel')
    def handleCancel(self, action):
        self.request.response.setStatus(304);

    @z3c.form.button.buttonAndHandler(_(u'Yes, I\'m sure'), name='delete')
    def handleDelete(self, action):
        Session = named_scoped_session(self.context.session)
        Session.delete(self.context.item)
        Session.flush()
        self.context._data = None
        self.request.response.setStatus(200)


# Need to wrap the form because of the custom template
FieldDeleteFormView = plone.z3cform.layout.wrap_form(FieldDeleteForm)


class FieldOrderForm(StandardWidgetsMixin, z3c.form.form.Form):
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
        schemaContext = closest(self.context, ISchemaContext)

        self.fields = z3c.form.field.Fields(zope.schema.Choice(
            __name__='target',
            title=_(u'Target Fieldset'),
            description=_(
                u'The fieldset within the parent form to send the field to.'
                ),
            values=listFieldsets(schemaContext.data),
            required=False,
            ))

        self.fields += z3c.form.field.Fields(zope.schema.ASCIILine(
            __name__='after',
            title=_(u'After which field'),
            required=False,
            ))

        super(FieldOrderForm, self).update()

    @z3c.form.button.buttonAndHandler(title=_(u'Sort'), name='apply')
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.request.response.setStatus(400)
        else:
            (target, after) = (data['target'], data['after'])
            parent = self.context.getParentNode()
            schemaContext = closest(self.context, ISchemaContext)
            sourceForm = parent.item
            Session = named_scoped_session(self.context.session)
            # Get the target form data that the field is going to
            if target:
                targetForm = schemaContext.item[target]
            else:
                targetForm = schemaContext.item
            if targetForm == sourceForm:
                moveField(targetForm, self.context.item, after)
                self.context._data = None
            elif self.context.item in targetForm.values():
            # Do not allow the field to be moved into another schema if it
            # already contains a field with the same name
                self.request.response.setStatus(400)
            else:
                # This item needs to move to a different fieldset
                field = self.context.item
                del sourceForm[self.context.item.name]
                parent._data = None
                targetForm[field.name] = field
                moveField(targetForm, field, after)
                schemaContext._data = None
                self.context._data = None
            Session.flush()
            self.request.response.setStatus(200)


    def render(self):
        return u''


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
            fields = z3c.form.field.Fields(schema).select('name', 'title', 'description')
            fields['description'].widgetFactory = TextAreaFieldWidget
            if 'choices' in schema:
                fields += z3c.form.field.Fields(schema).select('choices')
                fields['choices'].widgetFactory = DataGridFieldFactory
            fields += z3c.form.field.Fields(schema).omit('name', 'title', 'description', 'choices')
            self._fields = fields
        return self._fields

    def datagridInitialise(self, subform, widget):
        """
        Callback for configuring grid widgets
        """
        # Booleans are not allowed to have more than two values (duh)
        if self.getType() == 'boolean':
            subform.fields['value'].widgetFactory = TextFieldWidget
            widget.auto_append = False
            widget.allow_insert = False
            widget.allow_delete = False
            widget.allow_reorder = False
        else:
            widget.allow_reorder = True
            widget.auto_append = True
            widget.allow_insert = True
            widget.allow_delete = True

    def datagridUpdateWidgets(self, subform, widgets, widget):
        """
        Callback for updating grid widgets
        """
        # Booleans are special in that their values are known
        if self.getType() == 'boolean':
            widgets['value'].readonly = 'readonly'

from occams.datastore import model

class FieldAddForm(FieldFormInputHelper, z3c.form.form.AddForm):
    """
    Add form for fields.

    Optionally takes a request variable ``order`` to preset where the
    field will be added (otherwise at the end of the form)
    """
    z3c.form.form.extends(z3c.form.form.AddForm)

    prefix = 'add'

    @property
    def label(self):
        return _('New %s Field') % typesVocabulary.getTermByToken(self.typeName).title

    def getType(self):
        return self.__name__.split('-').pop()

    def update(self):
        self.request.set('disable_border', True)
        # Can't add fields to non-object fields
        if IAttributeContext.providedBy(self.context) and \
                self.context['type'] != 'object':
            raise NotFound()

        self.buttons = self.buttons.select('cancel', 'add')

        self.fields = self.getMetadataFields().omit('order')

        self.fields += z3c.form.field.Fields(zope.schema.ASCIILine(
            __name__='after',
            title=_(u'After which field'),
            required=False,
            ))

        super(FieldAddForm, self).update()

    def updateWidgets(self):
        super(FieldAddForm, self).updateWidgets()

        # Set the order (this is intended for AJAX requests)
        if 'after' in self.request:
            self.widgets['after'].value = str(self.request.get('after', ''))

        self.widgets['after'].mode = HIDDEN_MODE

        # Set the boolean default if not already set
        if self.getType() == 'boolean' and not self.widgets['choices'].value:
            self.widgets['choices'].value = [
                dict(title=u'True', value=True),
                dict(title=u'False', value=False),
                ]

    def create(self, data):
        cleanupChoices(data)
        newSchema = None
        if self.getType() == 'object':
            ## Need to create a new schema and a new Attribute
            newSchema = model.Schema(
                    name = self.context.__name__ + camelize(data['title']),
                    title = data['title'],
                    description = data['description'],
                    is_inline = True
                )

        newAttribute = model.Attribute(
                name=str(data['name']).lower(),
                title=data['title'],
                description=data['description'],
                is_collection= data.get('is_collection', False),
                is_required=data.get('is_collection', False),
                type = self.getType(),
                object_schema = newSchema
                )
        if data.has_key('choices') and data['choices']:
            applyChoiceChanges(newAttribute, data['choices'])

        newAttribute._after = data['after']
        return newAttribute

    def add(self, item):
        if IAttributeContext.providedBy(self.context):
            form = self.context.item.object_schema
        else:
            form = self.context.item
        # The after property is no longer needed
        after = item._after
        del item._after
        form[item.name] = item
        moveField(form, item, after)
        Session = named_scoped_session(self.context.session)
        Session.add(form)
        Session.flush()
        self._newItem = item

    def nextURL(self):
        url = self.context.absolute_url()
        if self._newItem is not None:
            url = os.path.join(url, str(self._newItem.name), '@@json')
        return url

    @z3c.form.button.buttonAndHandler(_(u'Cancel'), name='cancel')
    def handleCancel(self, action):
        self._finishedAdd = True

class FieldEditForm(FieldFormInputHelper, z3c.form.form.EditForm):
    """
    Edit form for field.
    """
    z3c.form.form.extends(z3c.form.form.EditForm)

    prefix = 'edit'

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
        # Flip the buttons
        self.buttons = self.buttons.select('cancel', 'apply')
        self.buttons['apply'].title = _(u'Apply')
        self.fields['order'].mode = HIDDEN_MODE
        super(FieldEditForm, self).update()

    def updateWidgets(self):
        super(FieldEditForm, self).updateWidgets()
        self.widgets['name'].readonly = 'readonly'

    def applyChanges(self, data):
        """
        Commits changes to the browser session data
        """

        cleanupChoices(data)
        # Now do the default changes
        changes = super(FieldEditForm, self).applyChanges(data)
        if changes:
            Session = named_scoped_session(self.context.session)
            # Get into the heart of the changes
            for changelist in changes.values():
                ## outputes lists, so go through them:
                for change in changelist:
                    if change == 'choices':
                        applyChoiceChanges(self.context.item, data[change])
                    else:
                        setattr(self.context.item, change, data[change])
            Session.flush()
        self.context._data = None
        nextUrl = os.path.join(self.context.absolute_url(), '@@json')
        self.request.response.redirect(nextUrl)
        return changes

    @z3c.form.button.buttonAndHandler(_(u'Cancel'), name='cancel')
    def handleCancel(self, action):
        parent = self.context.getParentNode()
        nextUrl = os.path.join(parent.absolute_url())
        self.request.response.redirect(nextUrl)


class VariableNameValidator(z3c.form.validator.SimpleFieldValidator):
    """
    Variable name validation
    """

    def validate(self, value):
        super(VariableNameValidator, self).validate(value)

        # We want lower case, so validate as such (will be forced on add)
        value = value.lower()

        # Check proper Python variable name
        if value != symbolize(value):
            raise zope.interface.Invalid(_(u'Not a valid variable name'))

        if IAttributeContext.providedBy(self.context):
            schemaData = self.context.data['schema']
        else:
            schemaData = self.context.data

        if value in reservedWords:
            raise zope.interface.Invalid(_(u'Can\'t use reserved programming word'))

        # Avoid duplicate variable names
        if value in schemaData['fields']:
            raise zope.interface.Invalid(_(u'Variable name already exists in this form'))


# Limit variable name validation only to add forms, since that's the only time
# a user is allow to choose a name
z3c.form.validator.WidgetValidatorDiscriminators(
    validator=VariableNameValidator,
    view=FieldAddForm,
    field=IEditableField['name'],
    )


class ConstraintValidator(z3c.form.validator.SimpleFieldValidator):
    """
    Field constraints validation
    """

    def validate(self, value):
        super(ConstraintValidator, self).validate(value)
        if value:
            values = [c['value'] for c in value]
            titles = [c['title'] for c in value]
            if len(values) != len(set(values)) or len(titles) != len(set(titles)):
                raise zope.interface.Invalid(_(
                    u'Only unique values and titles are allowed'
                    ))


# Limit the contraint validator to only forms that will be dealing with
# field metadata (add/edit)
z3c.form.validator.WidgetValidatorDiscriminators(
    validator=ConstraintValidator,
    view=FieldFormInputHelper,
    widget=DataGridField
    )


