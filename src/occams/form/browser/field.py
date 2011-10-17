from five import grok
from plone.directives import form

from occams.form.interfaces import IOccamsBrowserView
from occams.form.interfaces import IAttributeContext


class EditForm(form.Form):
    grok.implements(IOccamsBrowserView)
    grok.context(IAttributeContext)
    grok.name('edit')
    grok.require('occams.form.ModifyForm')

    @property
    def label(self):
        return 'Edit: %s' % self.context.item.title

    def update(self):
        self.request.set('disable_border', True)
        super(EditForm, self).update()
