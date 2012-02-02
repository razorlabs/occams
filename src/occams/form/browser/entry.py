"""
Form data entry tools
"""

import zope.schema
import z3c.form.form
import z3c.form.group

from avrc.data.store.interfaces import IDataStore
from occams.form.browser.widgets import fieldWidgetMap


class StandardForm(object):
    """
    Renders a standard OCCAMS form
    """

    def update(self):
        for field in self.fields.values():
            widgetFactory = fieldWidgetMap.get(field.field.__class__)
            if widgetFactory:
                field.widgetFactory = widgetFactory
        super(StandardForm, self).update()


class DisabledForm(object):
    """
    Disables all widgets in the form
    """

    def updateWidgets(self):
        super(DisabledForm, self).updateWidgets()
        for widget in self.widgets.values():
            widget.disabled = 'disabled'


class FormPreviewGroup(StandardForm, DisabledForm, z3c.form.group.Group):
    """
    Renders the "fieldset" parts of the form
    """


class FormPreview(StandardForm, DisabledForm, z3c.form.group.GroupForm, z3c.form.form.Form):
    """
    Renders the form as it would appear during data entry
    """

    ignoreContext = True
    ignoreRequest = True

    enable_form_tabbing = False

    @property
    def label(self):
        return self.context.title

    @property
    def description(self):
        return self.context['description']

    def update(self):
        self.request.set('disable_border', True)
        repository = self.context.getParentNode()

        form = IDataStore(repository).schemata.get(self.context.__name__)

        self.fields = z3c.form.field.Fields()
        self.groups = []

        def overrideWidgets(fields):
            for field in fields.values():
                widgetFactory = fieldWidgetMap.get(field.field.__class__)
                if widgetFactory:
                    field.widgetFactory = widgetFactory

        for name, field in zope.schema.getFieldsInOrder(form):
            if isinstance(field, zope.schema.Object):
                group = FormPreviewGroup(None, self.request, self)
                group.prefix = field.__name__
                group.label = field.title
                group.description = field.description
                group.fields = z3c.form.field.Fields(field.schema)
                self.groups.append(group)
                overrideWidgets(group.fields)
            else:
                self.fields += z3c.form.field.Fields(field)

        overrideWidgets(self.fields)

        super(FormPreview, self).update()

