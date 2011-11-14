"""
Custom widget behavior.
"""

from five import grok
import z3c.form.browser.textarea
import z3c.form.widget

from occams.form.interfaces import IOccamsBrowserView


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
