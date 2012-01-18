"""
Custom widget behavior.
"""

import zope.schema

import z3c.form.browser.textarea
from z3c.form.browser.radio import RadioFieldWidget
from z3c.form.browser.checkbox import CheckBoxFieldWidget

from occams.form.interfaces import TEXTAREA_SIZE


def TextAreaFieldWidget(field, request):
    """
    z3c.form doesn't allow configuring of rows so we must subclass it.

    Unfortunately there is no way to register this, so every view that wants
    to use this factory must specify it in the ``widgetFactory`` property
    of the ``z3c.form.field.Field`` instance.
    """
    widget = z3c.form.browser.textarea.TextAreaFieldWidget(field, request)
    widget.rows = TEXTAREA_SIZE
    return widget


fieldWidgetMap = {
    zope.schema.Choice: RadioFieldWidget,
    zope.schema.List: CheckBoxFieldWidget,
    zope.schema.Text: TextAreaFieldWidget,
    }
