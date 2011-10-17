
from five import grok

from occams.form import MessageFactory as _
from occams.form.interfaces import IOccamsBrowserView
from occams.form.interfaces import ISchemaContext
from occams.form.interfaces import IEntityContext


class Listing(grok.View):
    grok.implements(IOccamsBrowserView)
    grok.context(ISchemaContext)
    grok.name('data')
    grok.require('occams.form.ViewEntry')

    def update(self):
        self.request.set('disable_border', True)
        super(Listing, self).update()
