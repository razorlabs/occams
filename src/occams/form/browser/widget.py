"""
Custom widget behavior.
"""

from five import grok
from z3c.form.widget import StaticWidgetAttribute
import z3c.form.browser.textarea

from occams.form.interfaces import IOccamsBrowserView


# Enable prompt for widgets even if they are required, to prevent the users
# from cruising through the form without consciously deciding which value 
# they actually want. 
# Example at:
# http://packages.python.org/z3c.form/browser/select.html#explicit-selection-prompt
overrideRequiredChoicePrompt = StaticWidgetAttribute(
    value=True,
    view=IOccamsBrowserView,
    )

grok.global_adapter(overrideRequiredChoicePrompt, name=u'prompt')


def TextAreaFieldWidget(field, request):
    """  
    z3c.form doesn't allow configuring of rows so we must subclass it
    """
    widget = z3c.form.browser.textarea.TextAreaFieldWidget(field, request)
    widget.rows = 10
    return widget
