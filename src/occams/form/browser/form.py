
from zope.publisher.interfaces import IPublishTraverse
from zExceptions import NotFound

from five import grok
from plone.directives import form

from avrc.data.store.interfaces import IDataStore
from avrc.data.store import directives as datastore

from occams.form.interfaces import IRepository
from occams.form.browser.render import convertSchemaToForm


class Preview(form.SchemaForm):
    """
    Displays a preview the form.
    This view should have no button handlers since it's only a preview of
    what the form will look like to a user. 
    """
    grok.implements(IPublishTraverse)
    grok.context(IRepository)
    grok.name('form')

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
        datastoreForm = IDataStore(self.context).schemata.get(self._formName)
        self._form = convertSchemaToForm(datastoreForm)
