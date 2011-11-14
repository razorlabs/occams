from five import grok
from plone.directives import form
from plone.directives import dexterity
from z3c.form import field

from occams.form.interfaces import IRepository
from occams.form.interfaces import IOccamsBrowserView


# NOTE: view is declared via ZCML


class Add(dexterity.AddForm):
    grok.name('occams.form.repository')
    grok.implements(IOccamsBrowserView)


class Edit(dexterity.EditForm):
    grok.context(IRepository)
    grok.implements(IOccamsBrowserView)
