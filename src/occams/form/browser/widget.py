"""
Custom widget behavior.
"""

import zope.schema
from five import grok
import z3c.form.browser.textarea
import z3c.form.widget
from z3c.form.browser.radio import RadioFieldWidget
from z3c.form.browser.checkbox import CheckBoxFieldWidget

from occams.form.interfaces import IOccamsBrowserView


# Enable prompt for widgets even if they are required, to prevent the users
# from cruising through the form without consciously deciding which value 
# they actually want. 
choicePrompt = z3c.form.widget.StaticWidgetAttribute(value=True, view=IOccamsBrowserView,)
grok.global_adapter(choicePrompt, name=u'prompt')


def TextAreaFieldWidget(field, request):
    """  
    z3c.form doesn't allow configuring of rows so we must subclass it.
    
    Unfortunately there is no way to register this, so every view that wants
    to use this factory must specify it in the ``widgetFactory`` property 
    of the ``z3c.form.field.Field`` instance.
    """
    widget = z3c.form.browser.textarea.TextAreaFieldWidget(field, request)
    widget.rows = 5
    return widget


fieldWidgetMap = {
    zope.schema.Choice: RadioFieldWidget,
    zope.schema.List: CheckBoxFieldWidget,
    zope.schema.Text: TextAreaFieldWidget,
    }
