from five import grok
from plone.directives import form
from plone.directives import dexterity
from z3c.form import field

from occams.form.interfaces import IRepository
from occams.form.interfaces import IOccamsBrowserView


class Add(dexterity.AddForm):
    grok.name('occams.form.repository')
    grok.implements(IOccamsBrowserView)


class Edit(dexterity.EditForm):
    grok.context(IRepository)
    grok.implements(IOccamsBrowserView)


#class View(grok.View):
#    grok.context(IChangeset)
#    grok.implements(IOccamsBrowserView)

