import os.path

from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.component import getUtility
from zope.interface import implements
import zope.schema
from zope.schema.interfaces import IVocabulary

from plone.z3cform import layout
from plone.z3cform.crud import crud
import z3c.form.button
import z3c.form.field
import z3c.form.group

from z3c.form.browser.radio import RadioFieldWidget
from z3c.form.browser.checkbox import CheckBoxFieldWidget

from avrc.data.store.interfaces import IDataStore
from avrc.data.store import directives as datastore


from occams.form import MessageFactory as _
from occams.form.browser.widget import TextAreaFieldWidget
from occams.form.interfaces import IOccamsBrowserView
from occams.form.interfaces import IFormSummary
from occams.form.interfaces import IFormSummaryGenerator


class ListingEditForm(crud.EditForm):
    """
    Custom form edit form.
    """
    label = None

    # No buttons for this release
    buttons = z3c.form.button.Buttons()


class SummaryListingForm(crud.CrudForm):
    """
    Lists the forms in the repository.
    No add form is needed as that will be a separate view.
    See ``configure.zcml`` for directive configuration.
    """

    addform_factory = crud.NullForm
    editform_factory = ListingEditForm

    # don't use changes count, apparently it's too confusing for users
    view_schema = z3c.form.field.Fields(IFormSummary).omit('name', 'changeCount')

    _items = None

    def get_items(self):
        """
        Return a listing of all the forms.
        """
        # Plone seems to call this method more than once, so make sure
        # we return an already generated listing.
        if self._items is None:
            datastore = IDataStore(self.context)
            generator = getUtility(IFormSummaryGenerator)
            listing = generator.getItems(datastore.session)
            self._items = [(summary.name, summary) for summary in listing]
        return self._items

    def link(self, item, field):
        """
        Renders a link to the form view
        """
        if field == 'title':
            # Redirect to the editor for now, until we can get some stats
            return os.path.join(self.context.absolute_url(), item.name, '@@edit')


class Listing(layout.FormWrapper):
    """
    Form wrapper so it can be rendered with a Plone layout and dynamic title.
    """
    implements(IOccamsBrowserView)

    form = SummaryListingForm

    @property
    def label(self):
        return self.context.title

    @property
    def description(self):
        return self.context.description


class SchemaEditForm(z3c.form.group.GroupForm, z3c.form.form.Form):
    """
    Displays a preview the form.
    
    A note on sub-objects: There currently seems to be too many caveats
    surrounding object widgets (see ``z3c.form.object``). Given that, we
    will be using z3c group forms to represent sub objects.
    """
    implements(IOccamsBrowserView)

    ignoreContext = True
    ignoreRequest = True

    enable_form_tabbing = False

    template = ViewPageTemplateFile('form_templates/edit.pt')

    groups = ()

    @property
    def label(self):
        return self.context.item.title

    @property
    def description(self):
        return self.context.item.description

    @property
    def prefix(self):
        return str(self.context.item.name)

    def types(self):
        """
        Template helper for types
        """
        types = getUtility(IVocabulary, 'avrc.data.store.Types')
        return types

    def update(self):
        self.request.set('disable_border', True)
        self._updateHelper()
        super(SchemaEditForm, self).update()

    @property
    def macros(self):
        return self.index.macros

    def _updateHelper(self):
        """
        Helper method for updating the fields/groups to render
        """
        repository = self.context.getParentNode()
        form = IDataStore(repository).schemata.get(self.context.item.name, None)

        defaultNames = []
        groups = []

        # We need a custom class for rendering disabled groups
        class DisabledGroup(z3c.form.group.Group):
            def updateWidgets(self):
                super(DisabledGroup, self).updateWidgets()
                # Disable fields since we're not actually entering data
                for widget in self.widgets.values():
                    widget.disabled = 'disabled'

        # Update each field/group
        for name, field in zope.schema.getFieldsInOrder(form):
            # Put each sub-object form in a group
            if isinstance(field, zope.schema.Object):
                group = DisabledGroup(None, self.request, self)
                group.label = field.title
                group.description = field.description
                group.prefix = name
                group.fields = z3c.form.field.Fields(field.schema)
                groups.append(group)
            else:
                defaultNames.append(name)

        defaultGroup = DisabledGroup(None, self.request, self)
        defaultGroup.label = '(Default)'
        defaultGroup.fields = z3c.form.field.Fields(form).select(*defaultNames)

        groups.insert(0, defaultGroup)
        self.groups = tuple(groups)

        # Override the complex widgets with some simple checkbox/radio ones
        for group in self.groups:
            self._overrideWidgets(group.fields)

    def _overrideWidgets(self, fields):
        """
        Helper method for overriding the form widgets with our own custom ones.
        """
        fieldWidgetMap = {
            zope.schema.Choice: RadioFieldWidget,
            zope.schema.List: CheckBoxFieldWidget,
            zope.schema.Text: TextAreaFieldWidget,
            }

        for field in fields.values():
            fieldType = field.field.__class__
            if fieldType in fieldWidgetMap:
                field.widgetFactory = fieldWidgetMap.get(fieldType)


class Edit(layout.FormWrapper):
    """
    """

    form = SchemaEditForm

    def label(self):
        return u'Edit: %s (%s)' % (self.context.item.title, self.context.item.name)
