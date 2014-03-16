"""
Cross-vendor compatibility functions
"""

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import FunctionElement


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
    return 'CAST(%s AS DATETIME)' % compiler.process(element.clauses)
