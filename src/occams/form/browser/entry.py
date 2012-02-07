"""
Form data entry tools
"""

import zope.schema
import z3c.form.form
import z3c.form.group

import avrc.data.store.directives
from occams.form.browser.widgets import fieldWidgetMap


class StandardWidgetsMixin(object):
    """
    Renders a standard OCCAMS form
    """

    def update(self):
        for field in self.fields.values():
            widgetFactory = fieldWidgetMap.get(field.field.__class__)
            if widgetFactory:
                field.widgetFactory = widgetFactory
        super(StandardWidgetsMixin, self).update()


class DisabledMixin(object):
    """
    Disables all widgets in the form
    """

    def updateWidgets(self):
        super(DisabledMixin, self).updateWidgets()
        for widget in self.widgets.values():
            widget.disabled = 'disabled'


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
        self.iface = self.context.getDataStore().schemata.get(self.context.__name__)
        self.fields = z3c.form.field.Fields()
        self.groups = []
        for name, field in zope.schema.getFieldsInOrder(self.iface):
            if isinstance(field, zope.schema.Object):
                self.groups.append(self.groupFactory(field, self.request, self))
            else:
                self.fields += z3c.form.field.Fields(field)
        super(Form, self).update()


class PreviewForm(DisabledMixin, Form):
    """
    Renders the form as it would appear during data entry
    """

    class PreviewGroup(DisabledMixin, Group):
        """
        Renders group in preview-mode
        """

    groupFactory = PreviewGroup


