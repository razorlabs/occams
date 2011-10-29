
from five import grok
from plone.directives import form
from plone.directives import dexterity
from z3c.form import field

from occams.form.interfaces import IChangeset
from occams.form.interfaces import IOccamsBrowserView


class Add(dexterity.AddForm):
    grok.name('occams.form.changeset')
    grok.implements(IOccamsBrowserView)


class Edit(dexterity.EditForm):
    grok.context(IChangeset)
    grok.implements(IOccamsBrowserView)


#class View(grok.View):
#    grok.context(IChangeset)
#    grok.implements(IOccamsBrowserView)

