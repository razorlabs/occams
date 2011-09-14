from zope.publisher.interfaces import IPublishTraverse
from zExceptions import NotFound

from z3c.form import button
from z3c.form import field

from five import grok
from plone.directives import form

from avrc.data.store.interfaces import ISchema

from hive.form.interfaces import IRepository

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

    @property
    def label(self):
        #TODO: should be form's title
        return 'Foo'

    @property
    def description(self):
        #TODO: should be form's description
        return 'Description'

    @property
    def fields(self):
        return field.Fields()

    def publishTraverse(self, request, name):
        if self.itemName is None:
            self.itemName = str(name)
            return self
        else:
            raise NotFound()

    def update(self):
        self.request.set('disable_border', True)
        return super(Preview, self).update()

#    def render(self):
#        from avrc.data.store import model
#        from avrc.data.store.interfaces import IDataStore
#        datastore = IDataStore(self.context)
#        session = datastore.session
#        schema = session.query(model.Schema).filter(model.Schema.asOf(None)).filter_by(name=self.itemName).first()
#        return "YOU ARE TRYING TO RENDER: %s" % schema.name

