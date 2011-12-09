import os.path

from zope.interface import implements
import zope.schema
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.vocabulary import SimpleTerm

import z3c.form.form
import z3c.form.button
import z3c.form.field

from collective.beaker.interfaces import ISession

from occams.form import MessageFactory as _
from occams.form.interfaces import SESSION_KEY
from occams.form.interfaces import IOccamsBrowserView
from occams.form.interfaces import IEditableField
from occams.form.interfaces import typesVocabulary
from occams.form.browser.widget import fieldWidgetMap
from occams.form.browser.widget import TextAreaFieldWidget


class FieldFormMixin(object):
    """
    Base class for repetitive junk
    """

    def __init__(self, context, request):
        super(FieldFormMixin, self).__init__(context, request)
        self.request.set('disable_border', True)


class View(FieldFormMixin, z3c.form.form.Form):
    implements(IOccamsBrowserView)

    @property
    def label(self):
        return self.context.item.name

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

        super(View, self).updateWidgets()

        for widget in self.widgets.values():
            widget.disabled = 'disabled'

import zope.interface
from collective.z3cform.datagridfield import DataGridFieldFactory, DictRow

#        choicesWidget.allow_insert = True  # Enable/Disable the insert button on the right 
#        choicesWidget.allow_delete = True  # Enable/Disable the delete button on the right 
#        choicesWidget.auto_append = False   # Enable/Disable the auto-append feature 
class IRow(zope.interface.Interface):
    title = zope.schema.TextLine(title=_(u'Displayed Label'))
    value = zope.schema.TextLine(title=_(u'Stored Value'),)

class BaseAdd(FieldFormMixin, z3c.form.form.AddForm):
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
                value_type=DictRow(schema=IRow),
                required=False,
                )
            )

    fields['description'].widgetFactory = TextAreaFieldWidget
    fields['choices'].widgetFactory = DataGridFieldFactory

    type_ = None

    @property
    def label(self):
        return _(u'New %s Field') % typesVocabulary.getTermByToken(self.type_).title

    def updateWidgets(self):
        super(BaseAdd, self).updateWidgets()
        self.widgets['choices'].allow_reorder = True


class AddBoolean(BaseAdd):
    type_ = 'boolean'


class AddInteger(BaseAdd):
    type_ = 'integer'


class AddDecimal(BaseAdd):
    type_ = 'decimal'


class AddString(BaseAdd):
    type_ = 'string'


class AddText(BaseAdd):
    type_ = 'text'


class AddDateTime(BaseAdd):
    type_ = 'datetime'


class AddTime(BaseAdd):
    type_ = 'time'


class AddObject(BaseAdd):
    type_ = 'object'


class Edit(FieldFormMixin, z3c.form.form.EditForm):
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
                value_type=DictRow(schema=IRow),
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

    @z3c.form.button.buttonAndHandler(_(u'Cancel'), name='cancel')
    def handleCancel(self, action):
        parent = self.context.getParentNode()
        self.request.response.redirect(os.path.join(parent.absolute_url(), '@@edit'))

    @z3c.form.button.buttonAndHandler(_('Apply'), name='apply')
    def handleApply(self, action):
        """
        Saves field changes to the browser session.
        """
        super(Edit, self).handleApply(action)
        if self.status == self.successMessage:
            self.request.response.redirect(os.path.join(self.context.absolute_url(), '@@view'))


class Order(object):
    pass


class Remove(object):
    pass
