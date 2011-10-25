import os
from copy import copy

from zope.component import getUtility
from zope.interface.interface import InterfaceClass
import zope.schema

from five import grok
from plone.directives import form
from plone.directives.form.schema import FIELDSETS_KEY
from plone.directives.form.schema import WIDGETS_KEY
from plone.supermodel.model import Fieldset
from plone.z3cform import layout
from plone.z3cform.crud import crud
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form import button
from z3c.form import field

from avrc.data.store.interfaces import IDataStore
from avrc.data.store import directives as datastore
from avrc.data.store import model

from occams.form import MessageFactory as _
from occams.form.interfaces import IOccamsBrowserView
from occams.form.interfaces import ISchemaContext
from occams.form.interfaces import IFormSummary
from occams.form.interfaces import IFormSummaryGenerator


# TODO: Print # of forms

class ListingEditForm(crud.EditForm):
    """
    Custom form edit form.
    """
    label = None

    # No buttons for this release
    buttons = button.Buttons()


class SummaryListingForm(crud.CrudForm):
    """
    Lists the forms in the repository.
    No add form is needed as that will be a separate view.
    See ``configure.zcml`` for directive configuration.
    """

    addform_factory = crud.NullForm
    editform_factory = ListingEditForm

    # don't use changes count, apparently it's too confusing for users
    view_schema = field.Fields(IFormSummary).omit('name', 'changeCount')

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
            return os.path.join(self.context.absolute_url(), item.name)


class SummaryListing(layout.FormWrapper):
    """
    Form wrapper so it can be rendered with a Plone layout and dynamic title.
    """
    grok.implements(IOccamsBrowserView)

    form = SummaryListingForm

    # http://plone.org/documentation/manual/plone-community-developer-documentation/forms/z3c.form#customizing-form-template
    index = ViewPageTemplateFile('form_templates/listing.pt')

    @property
    def label(self):
        return self.context.title

    @property
    def description(self):
        return self.context.description


class PreviewForm(form.SchemaForm):
    """
    Displays a preview the form.
    This view should have no button handlers since it's only a preview of
    what the form will look like to a user.
    """
    grok.implements(IOccamsBrowserView)
    grok.context(ISchemaContext)
    grok.name('preview')
    grok.require('occams.form.ViewForm')

    ignoreContext = True
    enable_form_tabbing = False

    @property
    def label(self):
        return self.context.item.title

    @property
    def description(self):
        return self.context.item.description

    @property
    def schema(self):
        return self._form

    def update(self):
        self.request.set('disable_border', True)
        self._setupForm()
        super(PreviewForm, self).update()

    def _setupForm(self):
        repository = self.context.getParentNode()
        datastoreForm = IDataStore(repository).schemata.get(self.context.item.name)
        self._form = _formRender(datastoreForm)


class Usage(grok.View):
    grok.implements(IOccamsBrowserView)
    grok.context(ISchemaContext)
    grok.name('index')
    grok.require('occams.form.ViewForm')

    def update(self):
        self.request.set('disable_border', True)
        super(Usage, self).update()


class EditForm(form.Form):
    grok.implements(IOccamsBrowserView)
    grok.context(ISchemaContext)
    grok.name('edit')
    grok.require('occams.form.ModifyForm')

    @property
    def label(self):
        return 'Edit: %s' % self.context.item.title

    def update(self):
        self.request.set('disable_border', True)
        super(EditForm, self).update()


# Should technically be some sort of adapter
fieldWidgetMap = {
    zope.schema.Choice: 'z3c.form.browser.radio.RadioFieldWidget',
    zope.schema.List: 'z3c.form.browser.checkbox.CheckBoxFieldWidget',
    zope.schema.Text: 'occams.form.browser.widget.TextAreaFieldWidget',
    }


def _formRender(sourceForm):
    """
    Helper method that converts a DataStore form to a Dexterity Form
    (since subforms aren't well supported)
    """
    directives = {FIELDSETS_KEY: [], WIDGETS_KEY: dict()}
    widgets = dict()
    fields = dict()
    order = 0

    for name, attribute in zope.schema.getFieldsInOrder(sourceForm):
        queue = list()
        if isinstance(attribute, zope.schema.Object):
            fieldset = Fieldset(
                __name__=attribute.__name__,
                label=attribute.title,
                description=attribute.description,
                fields=zope.schema.getFieldNamesInOrder(attribute.schema)
                )
            directives[FIELDSETS_KEY].append(fieldset)
            for subname, subfield in zope.schema.getFieldsInOrder(attribute.schema):
                queue.append(copy(subfield))
        else:
            queue.append(copy(attribute))

        for field in queue:
            order += 1
            widget = fieldWidgetMap.get(field.__class__)

            if widget is None:
                widget = datastore.widget.bind().get(field)

            if widget is not None:
                directives[WIDGETS_KEY][field.__name__] = widget
                widgets[field.__name__] = widget

            field.order = order
            fields[field.__name__] = field

    # We're only rendering so it's not necessary to get the hierarchy
    ploneForm = InterfaceClass(
        name=sourceForm.__name__,
        bases=[form.Schema],
        attrs=fields
        )

    for key, item in directives.items():
        ploneForm.setTaggedValue(key, item)

    return ploneForm
