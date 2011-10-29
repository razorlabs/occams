"""
Custom widget behavior.
"""

from zope.interface import implementsOnly

from five import grok
import z3c.form.browser.textarea
import z3c.form.widget

from occams.form.interfaces import IOccamsBrowserView
from occams.form.interfaces import IXmlWidget


# Enable prompt for widgets even if they are required, to prevent the users
# from cruising through the form without consciously deciding which value 
# they actually want. 
choicePrompt = z3c.form.widget.StaticWidgetAttribute(value=True, view=IOccamsBrowserView,)
grok.global_adapter(choicePrompt, name=u'prompt')


def TextAreaFieldWidget(field, request):
    """  
    z3c.form doesn't allow configuring of rows so we must subclass it
    """
    widget = z3c.form.browser.textarea.TextAreaFieldWidget(field, request)
    widget.rows = 10
    return widget


class XmlWidget(z3c.form.browser.textarea.TextAreaWidget):
    implementsOnly(IXmlWidget)

    klass = u'xml-widget'
    value = u''

    def update(self):
        super(z3c.form.browser.textarea.TextAreaWidget, self).update()
        z3c.form.browser.widget.addFieldClass(self)


def XmlFieldWidget(field, request):
    """IFieldWidget factory for XmlWidget."""
    return z3c.form.widget.FieldWidget(field, XmlWidget(request))
