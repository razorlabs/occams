"""
API base classes for rendering forms in certain contexts.
"""

import zope.schema
import z3c.form.form
import z3c.form.group
import z3c.form.browser.textarea
from z3c.form.browser.radio import RadioFieldWidget
from z3c.form.browser.checkbox import CheckBoxFieldWidget

import avrc.data.store.directives
from occams.form.interfaces import TEXTAREA_SIZE


def TextAreaFieldWidget(field, request):
    """
    Forms should use a slightly bigger textarea

    z3c.form doesn't allow configuring of rows so we must subclass it.

    Unfortunately there is no way to register this, so every view that wants
    to use this factory must specify it in the ``widgetFactory`` property
    of the ``z3c.form.field.Field`` instance.
    """
    widget = z3c.form.browser.textarea.TextAreaFieldWidget(field, request)
    widget.rows = TEXTAREA_SIZE
    return widget


fieldWidgetMap = {
    zope.schema.Choice: RadioFieldWidget,
    zope.schema.List: CheckBoxFieldWidget,
    zope.schema.Text: TextAreaFieldWidget,
    }


class StandardWidgetsMixin(object):
    """
    Updates form widgets to use basic widgets that make it easy for the user
    to distinguish available options.
    """

    def update(self):
        for field in self.fields.values():
            widgetFactory = fieldWidgetMap.get(field.field.__class__)
            if widgetFactory:
                field.widgetFactory = widgetFactory
        super(StandardWidgetsMixin, self).update()


class Group(StandardWidgetsMixin, z3c.form.group.Group):
    """
    A datastore-specific group
    """

    @property
    def prefix(self):
        return self.context.__name__

    @property
    def label(self):
        return self.context.title

    @property
    def description(self):
        return self.context.description

    def update(self):
        self.fields = z3c.form.field.Fields(self.context.schema)
        super(Group, self).update()


class Form(StandardWidgetsMixin, z3c.form.group.GroupForm, z3c.form.form.Form):
    """
    A datastore-specific form
    """

    ignoreContext = True
    ignoreRequest = True
    enable_form_tabbing = False

    iface = None
    groupFactory = Group

    @property
    def label(self):
        return avrc.data.store.directives.title.bind().get(self.iface)

    @property
    def description(self):
        return avrc.data.store.directives.description.bind().get(self.iface)

    def update(self):
        self.request.set('disable_border', True)
        # TODO: should be context-agnostic
        self.iface = self.context.getDataStore().schemata.get(self.context.__name__)
        self.fields = z3c.form.field.Fields()
        self.groups = []
        for name, field in zope.schema.getFieldsInOrder(self.iface):
            if isinstance(field, zope.schema.Object):
                self.groups.append(self.groupFactory(field, self.request, self))
            else:
                self.fields += z3c.form.field.Fields(field)
        super(Form, self).update()
