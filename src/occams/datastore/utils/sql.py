"""
Cross-vendor compatibility functions
"""

import json

from sqlalchemy import func, collate
from sqlalchemy.dialects import postgres
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import FunctionElement
from sqlalchemy.types import TypeDecorator, TEXT, VARCHAR


class group_concat(FunctionElement):
    """
    Generates delimitted list from a subquery.
    Parameters:
    expression -- The source subquery
    delimiter -- (Optional in sqlite) The delimiter to use
    """
    name = 'group_concat'


@compiles(group_concat)
@compiles(group_concat, 'sqlite')
def group_concat_sqlite(element, compiler, **kw):
    compiled = tuple(map(compiler.process, element.clauses))
    if len(compiled) == 2:
        return 'GROUP_CONCAT(%s, %s)' % compiled
    elif len(compiled) == 1:
        return 'GROUP_CONCAT(%s)' % compiled
    else:
        raise TypeError('Only 1 or 2 arguments supported SQLite')


@compiles(group_concat, 'postgresql')
def group_concat_pg(element, compiler, **kw):
    compiled = tuple(map(compiler.process, element.clauses))
    if len(compiled) == 2:
        return 'ARRAY_TO_STRING(ARRAY_AGG(%s), %s)' % compiled
    else:
        raise TypeError('Only 2 arguments supported in PostgreSQL')


class to_date(FunctionElement):
    """
    Generates a date converted value
    Parameters:
    expression -- The source subquery
    """
    name = 'to_date'


@compiles(to_date, 'sqlite')
def to_date_sqlite(element, compiler, **kw):
    return 'DATE(%s)' % compiler.process(element.clauses)


@compiles(to_date)
@compiles(to_date, 'postgresql')
def to_date_pg(element, compiler, **kw):
    return 'CAST(%s AS DATE)' % compiler.process(element.clauses)


class to_datetime(FunctionElement):
    """
    Generates a datetime converted value
    Parameters:
    expression -- The source subquery
    """
    name = 'to_date'


@compiles(to_datetime, 'sqlite')
def to_datetime_sqlite(element, compiler, **kw):
    return 'DATETIME(%s)' % compiler.process(element.clauses)


@compiles(to_datetime)
@compiles(to_datetime, 'postgresql')
def to_datetime_pg(element, compiler, **kw):
    return 'CAST(%s AS TIMESTAMP)' % compiler.process(element.clauses)


class JSON(TypeDecorator):
    """
    Represents an immutable structure as a json-encoded string.

    To make this type mutable, use the ``sqlalchemy.ext.mutable``.

    Uses PostgreSQL's native JSON types, otherwise falls back to
    a regulart TEXT field with the encoded JSON object.
    """

    impl = TEXT

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            impl = postgres.JSON()
        else:
            impl = TEXT()
        return dialect.type_descriptor(impl)

    def process_bind_param(self, value, dialect):
        if dialect.name != 'postgresql':
            if value is not None:
                value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if dialect.name != 'postgresql':
            if value is not None:
                value = json.loads(value)
        return value


class CaseInsensitive(FunctionElement):
    """
    Function for case insensite indexes
    """
    # Need this attribute so Index can processes this element
    # http://stackoverflow.com/q/22154917/148781
    __visit_name__ = 'notacolumn'
    name = 'CaseInsensitive'
    type = VARCHAR()


@compiles(CaseInsensitive, 'sqlite')
def case_insensitive_sqlite(element, compiler, **kw):
    arg1, = list(element.clauses)
    return compiler.process(collate(arg1, 'NOCASE'), **kw)


@compiles(CaseInsensitive, 'postgresql')
def case_insensitive_postgresql(element, compiler, **kw):
    arg1, = list(element.clauses)
    return compiler.process(func.lower(arg1), **kw)
