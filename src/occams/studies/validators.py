"""
Re-usable valiators
"""

from datetime import datetime
from voluptuous import Invalid


def Date(fmt='%Y-%m-%d', msg=None):
    def validator(value):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            raise Invalid(msg or u'Invalid date format, must be YYYY-MM-DD')
    return validator


def DateTime(fmt='%Y-%m-%d', msg=None):
    def validator(value):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            raise Invalid(msg or u'Invalid date format, must be YYYY-MM-DD')
    return validator
