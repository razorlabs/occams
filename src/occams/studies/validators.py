"""
Re-usable valiators
"""

from datetime import datetime, date
from voluptuous import Invalid

from . import Session


def Date(fmt='%Y-%m-%d', msg=None):
    def validator(value):
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            raise Invalid(msg or u'Invalid date format, must be YYYY-MM-DD')
    return validator


def DateTime(fmt='%Y-%m-%d', msg=None):
    def validator(value):
        # Check datetime first since datetime is a subclass of date
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            raise Invalid(msg or u'Invalid date format, must be YYYY-MM-DD')
    return validator


def DatabaseEntry(class_, path=None, msg=None, localizer=None):
    """
    Returns a validator that evaluates the value into a database record.

    Paramters
    class_ -- the SQLAlchemy model or table
    path -- (optional) path to report  on invalid
    msg -- (optional) error message to report on invalid
    localizer -- (optional) translator to evaludate `msg` on invalid
    """
    def validator(value):
        entry = Session.query(class_).get(int(value))
        if entry is None:
            final_msg = msg or u'Record not found'
            if localizer is not None:
                final_msg = localizer.translate(final_msg)
            raise Invalid(final_msg, path=path)
        return entry
    return validator
