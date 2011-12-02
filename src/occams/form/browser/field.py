import os.path

from zope.interface import implements
import zope.schema
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.vocabulary import SimpleTerm

import z3c.form.form
import z3c.form.button
import z3c.form.field

from collective.beaker.interfaces import ISession

from avrc.data.store.interfaces import typesVocabulary

from occams.form import MessageFactory as _
from occams.form.interfaces import SESSION_KEY
from occams.form.interfaces import IOccamsBrowserView
from occams.form.interfaces import IEditableField
from occams.form.browser.widget import fieldWidgetMap


class FieldFormMixin(object):
    """
    Base class for repetitive junk
    """

    def __init__(self, context, request):
        super(FieldFormMixin, self).__init__(context, request)
        self.request.set('disable_border', True)

    def getContent(self):
        formName = self.context.getParentNode().item.name
        fieldName = self.context.item.name
        browserSession = ISession(self.request)
        content = None
        for name, group in browserSession[SESSION_KEY]['groups'].items():
            if group['schema'] == formName:
                content = group['fields'][fieldName]
                break
        return content


class View(FieldFormMixin, z3c.form.form.Form):
    implements(IOccamsBrowserView)

    def __init__(self, context, request):
        super(View, self).__init__(context, request)

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

    @property
    def label(self):
        return self.context.item.name

    def updateWidgets(self):
        for field in self.fields.values():
            fieldType = field.field.__class__
            if fieldType in fieldWidgetMap:
                field.widgetFactory = fieldWidgetMap.get(fieldType)
        super(View, self).updateWidgets()
        for widget in self.widgets.values():
            widget.disabled = 'disabled'

class Add(FieldFormMixin, z3c.form.form.AddForm):
    implements(IOccamsBrowserView)

class Order(object):
    pass

class Remove(object):
    pass

class Edit(FieldFormMixin, z3c.form.form.EditForm):
    implements(IOccamsBrowserView)

    fields = z3c.form.field.Fields(IEditableField)

    @property
    def label(self):
        return 'Edit: %s' % self.context.item.name

    def updateWidgets(self):
        super(Edit, self).updateWidgets()
        # Disable the 'name' field since we're editing.
        # It would be nice if this was conditionally disabled based
        # on the role of whomever is editing (e.g. only admins can change it)
        self.widgets['name'].disabled = 'disabled'

    @z3c.form.button.buttonAndHandler(_(u'Cancel'), name='cancel')
    def handleCancel(self, action):
        parent = self.context.getParentNode()
        self.request.response.redirect(os.path.join(parent.absolute_url(), '@@edit'))

    @z3c.form.button.buttonAndHandler(_('Apply'), name='apply')
    def handleApply(self, action):
        """
        Saves field changes to the browser session.
        """
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
        else:
            changes = self.applyChanges(data)

            if changes:
                self.status = self.successMessage
                ISession(self.request).save()
            else:
                self.status = self.noChangesMessage

            self.request.response.redirect(os.path.join(self.context.absolute_url(), '@@view'))

