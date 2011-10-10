"""
Custom widget behavior.
"""

from z3c.form.widget import StaticWidgetAttribute

# Set prompt to always display (see ZCML for the registration)
AllowPrompt = StaticWidgetAttribute(True)
