from zope.publisher.interfaces import IPublishTraverse
from zExceptions import NotFound

from z3c.form import field

from five import grok
from plone.directives import form

from avrc.data.store.interfaces import IDataStore
from avrc.data.store import directives as ds

from occams.form.interfaces import IRepository


class Preview(form.Form):
    """
    Displays a preview the form.
    This view should have no button handlers since it's only a preview of
    what the form will look like to a user. 
    """
    grok.implements(IPublishTraverse)
    grok.context(IRepository)
    grok.name('form')

    ignoreContext = True

    # Set by ``publishTraverse``
    itemName = None
    datastore = None
    form = None

    @property
    def label(self):
        return ds.title.bind().get(self.form)

    @property
    def description(self):
        return ds.description.bind().get(self.form)

    @property
    def fields(self):
        return field.Fields(self.form)

    def publishTraverse(self, request, name):
        self.Title = 'asdfsafsadf';
        if self.itemName is None:
            self.itemName = str(name)
            return self
        else:
            raise NotFound()

    def update(self):
        self.request.set('disable_border', True)
        self.setupForm()
        super(Preview, self).update()

    def setupForm(self):
        if self.datastore is None:
            self.datastore = IDataStore(self.context)

        self.form = self.datastore.schemata.get(self.itemName)
