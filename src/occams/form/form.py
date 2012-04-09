"""
API base classes for rendering forms in certain contexts.
"""
from AccessControl import getSecurityManager

from zope.schema.interfaces import IChoice
from zope.schema.interfaces import IList
from zope.schema.interfaces import ITextLine
from zope.schema.interfaces import IText
import z3c.form.form
import z3c.form.group
import z3c.form.browser.textarea
from z3c.form.browser.radio import RadioFieldWidget
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.browser.textlines import TextLinesFieldWidget
from zope.schema.interfaces import IField
from z3c.saconfig import named_scoped_session
from occams.datastore import model

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

class UserAwareMixin(object):
    """
    Verifies that the current user is in datastore
    """
    def update(self):
        if not hasattr(self, 'session'):
            if hasattr(self.context, 'session') and self.context.session:
                self.session = self.context.session
        if hasattr(self, 'session'):
            current_user = getSecurityManager().getUser().getId()
            Session = named_scoped_session(self.context.session)
            if current_user and Session.query(model.User).filter(model.User.key == current_user).first():
                Session.add(model.User(key=current_user))
                Session.flush()
        super(UserAwareMixin, self).update()


class StandardWidgetsMixin(object):
    """
    Updates form widgets to use basic widgets that make it easy for the user
    to distinguish available options.
    """

    def update(self):
        for field in self.fields.values():
            if IChoice.providedBy(field.field):
                field.widgetFactory = RadioFieldWidget
            elif IList.providedBy(field.field):
                if IChoice.providedBy(field.field.value_type):
                    field.widgetFactory = CheckBoxFieldWidget
                elif ITextLine.providedBy(field.field.value_type):
                    field.widgetFactory = TextLinesFieldWidget
            elif IText.providedBy(field.field) and not ITextLine.providedBy(field.field):
                field.widgetFactory = TextAreaFieldWidget
        super(StandardWidgetsMixin, self).update()


class Group(StandardWidgetsMixin, z3c.form.group.Group):
    """
    A datastore-specific group
    """

    @property
    def prefix(self):
        return str(self.context.name)

    @property
    def label(self):
        return self.context.title

    @property
    def description(self):
        return self.context.description

    def update(self):
        self.fields = z3c.form.field.Fields()
        for name, field in self.context.items():
            self.fields += z3c.form.field.Fields(IField(field))
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
        return self.iface['title']

    @property
    def description(self):
        return self.iface['description']

    def update(self):
        self.request.set('disable_border', True)
        # TODO: should be context-agnostic
        self.fields = z3c.form.field.Fields()
        self.groups = []
        for name, field in self.context.item.items():
            if field.type == 'object':
                self.groups.append(self.groupFactory(field.object_schema, self.request, self))
            else:
                self.fields += z3c.form.field.Fields(IField(field))
        super(Form, self).update()
