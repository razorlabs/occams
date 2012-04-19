"""
A utility for allowing the access of entered schema data to be represented
in a SQL table-like fashion.
"""

from occams.datastore import model


def schemaToSubQuery(session, name, split=False):
    """
    Returns a schema entity data as an aliased sub-query.

    Arguments
        ``name``
            The name of the schema family to generate the subquery for
        ``split``
            Optional parameter to split aggressively split the variable
            names by checksum. False by default.

    Returns
        A subquery representation of the schema family
    """

    schemaQuery = (
        session.query(model.Schema)
        .filter(model.Schema.name == name)
        .filter(model.Schema.publish_date != None)
        .order_by(model.Schema.publish_date.asc())
        )

    exportQuery = (
        session.query(
            model.Entity.id.label('entity_id'),
            model.Entity.state.label('entity_state'),
            model.Entity.collect_date.label('entity_collect_date'),
            )
        .join(model.Entity.schema)
        .filter(model.Schema.name == name)
        )

    names = set([])

    for schema in schemaQuery:
        pass

    subQuery = exportQuery.subquery(name)
    return subQuery
