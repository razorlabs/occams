"""
Re-usable valiators
"""

import six
from good import Invalid, All, Coerce, Type
from good.schema.util import const

from . import _, Session


ERROR_NOT_FOUND = _(u'Database record was not found')
ERROR_NOT_EXISTS = _(u'Database record does not exist')


def invalid2dict(exc):
    """
    Helper method to compile errors into a parseable error data sturcture
    """
    return dict(('.'.join(map(str, e.path)), e.message) for e in exc)


def List(value):
    """
    Forces a scalar into a list
    """
    if value is None or value is const.UNDEFINED:
        raise Invalid('List value is not defined')
    return [value] if not isinstance(value, list) else value


def Key(key):
    def validator(value):
        if not isinstance(value, dict):
            raise Invalid('not a dict')
        if key not in value:
            raise Invalid('%s is not in dict' % key)
        return value[key]
    return validator


def Bytes():
    return All(Type(*six.string_types), Coerce(six.binary_type))


def String():
    return All(Type(*six.string_types), Coerce(six.text_type))


def Integer():
    return Coerce(int)


def Sanitize():
    def validator(value):
        if value is not None:
            return value.strip() or None
    return validator


def Model(class_, path=None, msg=None, localizer=None):
    """
    Returns a validator that evaluates the value into a database record.

    Paramters
    class_ -- the SQLAlchemy model or table
    path -- (optional) path to report  on invalid
    msg -- (optional) error message (i18n-compatible) to report on invalid
    localizer -- (optional) translator to evaludate `msg` on invalid
    """
    def validator(value):
        entry = Session.query(class_).get(value)
        if entry is None:
            final_msg = msg or ERROR_NOT_FOUND
            if localizer is not None:
                final_msg = localizer.translate(final_msg)
            raise Invalid(final_msg, path=path)
        return entry
    return validator


def Exists(class_, path=None, msg=None, localizer=None):
    """
    Returns a validator that checks if a database record with value id exists.

    Paramters
    class_ -- the SQLAlchemy model or table
    path -- (optional) path to report  on invalid
    msg -- (optional) error message (i18n-compatible) to report on invalid
    localizer -- (optional) translator to evaludate `msg` on invalid
    """

    def validator(value):
        query = Session.query(class_).filter_by(id=value)
        (exists,) = Session.query(query.exists()).one()
        if not exists:
            final_msg = msg or ERROR_NOT_EXISTS
            if localizer is not None:
                mapping = {'id': value}
                final_msg = localizer.translate(final_msg, mapping=mapping)
            raise Invalid(final_msg, path=path)
        return value
    return validator
