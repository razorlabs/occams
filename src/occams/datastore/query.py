"""
A utility for allowing the access of entered schema data to be represented
in a SQL table-like fashion.
"""

from sqlalchemy.orm import object_session

from occams.datastore import model
from occams.datastore.schema import SchemaManager


def schemaByNameToSubQuery(session, name, on=None):
    """
    Returns a schema entity data as an aliased sub-query.

    Arguments
        ``session``
            The session containing the schema data
        ``name``
            The name of the schema
        ``on``
            (Optional) The target publish date, if none exists or ``None`` is
            specified, the most recent schema will be used.
    """
    return schemaToSubQuery(SchemaManager(session).get(name, on))


def schemaToSubQuery(schema):
    """
    Returns a schema entity data as an aliased sub-query.

    Arguments
        ``schema``
            The schema to use for generating the sub-query
    """
    session = object_session(schema)
    query = session.query(model.Entity)

    subquery = query.subquery(schema.name)
    return subquery
