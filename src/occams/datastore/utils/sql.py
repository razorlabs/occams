"""
Cross-vendor compatibility functions
"""

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import FunctionElement


class list_concat(FunctionElement):
    """
    Generates delimitted list from a subquery.
    Parameters:
    expression -- The source subquery
    delimiter -- (Optional in sqlite) The delimiter to use
    """
    name = 'list_concat'


@compiles(list_concat)
def list_concat_sqlite(element, compiler, **kw):
    compiled = tuple(map(compiler.process, element.clauses))
    if len(compiled) == 2:
        return 'GROUP_CONCAT(%s, %s)' % compiled
    elif len(compiled) == 1:
        return 'GROUP_CONCAT(%s)' % compiled
    else:
        raise TypeError('Only 1 or 2 arguments supported generically')


@compiles(list_concat, 'postgresql')
def list_concat_pg(element, compiler, **kw):
    compiled = tuple(map(compiler.process, element.clauses))
    if len(compiled) == 2:
        return 'ARRAY_TO_STRING(ARRAY(%s), %s)' % compiled
    else:
        raise TypeError('Only 2 arguments supported in PostgreSQL')
