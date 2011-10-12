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
from avrc.data.store.interfaces import ISchema
from avrc.data.store import directives as datastore

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


from zope.interface import Interface

class ISchemaContext(Interface):
    pass

class Preview(form.SchemaForm):
    """
    Displays a preview the form.
    This view should have no button handlers since it's only a preview of
    what the form will look like to a user. 
    
    TODO: Currently suffers from (http://dev.plone.org/plone/ticket/10699)
    """
#    grok.implements(IPublishTraverse, IOccamsBrowserView)
    grok.implements(IOccamsBrowserView)
    grok.context(ISchemaContext)
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

#    def publishTraverse(self, request, name):
#        import pdb; pdb.set_trace()
#        if self._formName is None:
#            self._formName = str(name)
#            return self
#        else:
#            raise NotFound()

    def update(self):
        self.request.set('disable_border', True)
        self._setupForm()
        super(Preview, self).update()

    def _setupForm(self):
        if self._form is None:
            datastoreForm = IDataStore(self.context).schemata.get(self._formName)
            self._form = convertSchemaToForm(datastoreForm)
            self.__name__ = self.label



import os

from plone.z3cform import layout
from plone.z3cform.crud import crud
from z3c.form import field

from avrc.data.store import model

from occams.form.interfaces import IFormSummary


# TODO: Print # of forms

class ListingEditForm(crud.EditForm):
    """
    Custom form edit form.
    """
    label = None
    buttons = crud.EditForm.buttons.copy()
    handlers = crud.EditForm.handlers.copy()


class Listing(crud.CrudForm):
    """
    Lists the forms in the repository.
    No add form is needed as that will be a separate view.
    See ``configure.zcml`` for directive configuration.
    """

    addform_factory = crud.NullForm
    editform_factory = ListingEditForm
    view_schema = field.Fields(IFormSummary)

    def get_items(self):
        """
        Return a listing of all the forms.
        """
        datastore = IDataStore(self.context)
        session = datastore.session
        query = (
            session.query(model.Schema)
            .filter(model.Schema.asOf(None))
            .order_by(model.Schema.name.asc())
            )
        items = [(str(schema.name), IFormSummary(schema)) for schema in query.all()]
        return items

    def link(self, item, field):
        """
        Renders a link to the form view
        """
        if field == 'title':
            return os.path.join(self.context.absolute_url(), item.context.name)

class ListingPage(layout.FormWrapper):
    """
    Form wrapper so it can be rendered with a Plone layout and dynamic title.
    """
    grok.implements(IOccamsBrowserView)

    form = Listing

    @property
    def label(self):
        return self.context.title

    @property
    def description(self):
        return self.context.description



from OFS.SimpleItem import SimpleItem


from zope.publisher.interfaces import IPublishTraverse
from zExceptions import NotFound

from avrc.data.store.interfaces import ISchema

class SchemaContext(SimpleItem):
    grok.implements(ISchemaContext)

    _schema = None


    def getSchema(self):
        return self._schema

from zope.traversing.interfaces import ITraversable

from occams.form.interfaces import IRepository


#from occams.form.browser.traverser import Traverser
from zope.publisher.interfaces.http import IHTTPRequest
from zope.publisher.interfaces.browser import IBrowserPublisher

class RepositoryContext(grok.MultiAdapter):
    grok.adapts(IRepository, IHTTPRequest)
    grok.implements(IBrowserPublisher)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def browserDefault(self, request):
        import pdb; pdb.set_trace()
        print 'adfadsfasdfas'

    def publishTraverse(self, request, name):
        import pdb; pdb.set_trace()
        return ListingPage(self.context, request)



#class Viewlets(SimpleItem):
#    """ Expose arbitary viewlets to traversing by name.
#
#    Exposes viewlets to templates by names.
#
#    Example how to render plone.logo viewlet in arbitary template code point::
#
#        <div tal:content="context/@@viewlets/plone.logo" />
#
#    """
#
#    ...




#
#        viewlet = self.setupViewletByName(name)
#        if viewlet is None:
#            active_layers = [ str(x) for x in self.request.__provides__.__iro__ ]
#            active_layers = tuple(active_layers)
#            raise ViewletNotFoundException("Viewlet does not exist by name %s for the active theme layer set %s. Probably theme interface not registered in plone.browserlayers. Try reinstalling the theme." % (name, str(active_layers)))
#
#        viewlet.update()
#        return viewlet.render()
#
#    def publishTraverse(self, request, name):
#        """ 1. Try to find a content type whose name matches the next URL path element.
#            2. Look up its schema.
#            3. Return a schema context (an acquisition-aware wrapper of the schema).
#        """
#        import pdb; pdb.set_trace()
#        if name is not None and name != 'index_html':
#            schema = None
#
#            if schema is None:
#                raise NotFound
#
#            view = SchemaContext(schema, request).__of__(self.context)
#
#        else:
#            view = ListingPage(self.context, request).__of__(self.context)
#        return view
#        try:
#            fti = getUtility(IDexterityFTI, name=name)
#        except ComponentLookupError:
#            raise NotFound
#
#        schema = fti.lookupSchema()
#        schema_context = TypeSchemaContext(schema, request, name=name, title=fti.title).__of__(self)
#        schema_context.fti = fti
#        schema_context.schemaName = u''
#        return schema_context
