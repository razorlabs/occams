from copy import copy

from zope.interface.interface import InterfaceClass
import zope.schema
from zope.publisher.interfaces import IPublishTraverse
from zExceptions import NotFound

from five import grok
from plone.directives import form
from plone.directives.form.schema import FIELDSETS_KEY
from plone.directives.form.schema import WIDGETS_KEY
from plone.supermodel.model import Fieldset
from z3c.form import field

from avrc.data.store.interfaces import IDataStore
from avrc.data.store import directives as datastore

from occams.form.interfaces import IRepository
from occams.form.interfaces import IOccamsBrowserView

# TODO: PDF view
# Expand drop down widgets

def convertSchemaToForm(schema):
    """
    Converts a DataStore form to a Dexterity Form
    (since subforms aren't well supported)
    """
    if datastore.Schema not in schema.getBases():
        bases = [convertSchemaToForm(base) for base in schema.getBases()]
    else:
        bases = [form.Schema]

    directives = {FIELDSETS_KEY: [], WIDGETS_KEY: dict()}
    widgets = dict()
    fields = dict()
    order = 0

    for name, attribute in zope.schema.getFieldsInOrder(schema):
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
            widget = datastore.widget.bind().get(field)

            # TODO: there has to be some way to set these in the zcml...
            if isinstance(field, zope.schema.Choice):
                widget = 'z3c.form.browser.radio.RadioFieldWidget'
            elif isinstance(field, zope.schema.List):
                widget = 'z3c.form.browser.checkbox.CheckBoxFieldWidget'
            elif isinstance(field, zope.schema.Text):
                widget = 'occams.form.browser.widget.TextAreaFieldWidget'
            elif widget is not None and 'z3c' not in widget:
                # use custom ones, but this will be deprecated...
                pass
            else:
                # get rid of anything else
                widget = None

            if widget is not None:
                directives[WIDGETS_KEY][field.__name__] = widget
                widgets[field.__name__] = widget

            field.order = order
            fields[field.__name__] = field

    ploneForm = InterfaceClass(
        __doc__=schema.__doc__,
        name=schema.__name__,
        bases=bases,
        attrs=fields,
        )

    for key, item in directives.items():
        ploneForm.setTaggedValue(key, item)

    datastore.title.set(ploneForm, datastore.title.bind().get(schema))
    datastore.description.set(ploneForm, datastore.title.bind().get(schema))
    datastore.version.set(ploneForm, datastore.version.bind().get(schema))

    return ploneForm


class Preview(form.SchemaForm):
    """
    Displays a preview the form.
    This view should have no button handlers since it's only a preview of
    what the form will look like to a user. 
    
    TODO: Currently suffers from (http://dev.plone.org/plone/ticket/10699)
    """
    grok.implements(IPublishTraverse, IOccamsBrowserView)
    grok.context(IRepository)
    grok.name('form')
    grok.require('occams.form.ViewForm')

    ignoreContext = True
    enable_form_tabbing = False

    # Passed in URL
    _formName = None
    _version = None

    # Generated values from parameters
    _form = None

    @property
    def label(self):
        return datastore.title.bind().get(self._form)

    @property
    def description(self):
        return datastore.description.bind().get(self._form)

    @property
    def schema(self):
        return self._form

    def publishTraverse(self, request, name):
        if self._formName is None:
            self._formName = str(name)
            return self
        else:
            raise NotFound()

    def update(self):
        self.request.set('disable_border', True)
        self._setupForm()
        super(Preview, self).update()

    def _setupForm(self):
        if self._form is None:
            datastoreForm = IDataStore(self.context).schemata.get(self._formName)
            self._form = convertSchemaToForm(datastoreForm)
            self.__name__ = self.label
