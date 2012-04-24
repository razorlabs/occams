"""
A utility for allowing the access of entered schema data to be represented
in a SQL table-like fashion.
"""

from sqlalchemy import cast
from sqlalchemy.ext import compiler
from sqlalchemy.sql import ColumnElement
from sqlalchemy.orm import aliased

from occams.datastore.interfaces import InvalidEntitySchemaError
from occams.datastore import model
from occams.datastore.model.storage import nameCastMap
from occams.datastore.model.storage import nameModelMap


class Split(object):
    """
    An enum indicating how columns in the final sub-query should be split.
    Splitting algorithms are as follows:
        ``NAME``
            No splitting should occur, all attributes are grouped by their name
        ``CHECKSUM``
            All attributes are grouped by their checksum
        ``ID``
            Aggressively split by attribute id
    """

    (NAME, CHECKSUM, ID) = range(3)


def schemaToSubQuery(session, name, split=Split.NAME):
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

    # Collapse all the related attributes into an ordered tree
    names, columns = getAttributes(session, name, split=split)

    # TODO somewhere in here we further collapse the attributes based on a
    # configuration file

    exportQuery = (
        session.query(
            model.Entity.id.label('entity_id'),
            model.Entity.state.label('entity_state'),
            model.Entity.collect_date.label('entity_collect_date'),
            )
        .join(model.Entity.schema)
        .filter(model.Schema.name == name)
        .filter(model.Schema.publish_date != None)
        )

    for name in names:
        for attribute in columns[name]:

            Value = aliased(nameModelMap[attribute.type])

            if attribute.is_collection:
                column = collection(
                    session.query(cast(Value._value, nameCastMap[attribute.type]))
                    .filter(Value.entity_id == model.Entity.id)
                    .filter(Value.attribute_id == attribute.id)
                    .correlate(model.Entity)
                    .subquery()
                    .as_scalar()
                    )
            else:
                exportQuery = exportQuery.outerjoin(
                    Value,
                    ((Value.entity_id == model.Entity.id) &
                        (Value.attribute_id == attribute.id))
                    )

                column = cast(Value._value, nameCastMap[attribute.type])

            exportQuery = exportQuery.add_column(column.label(name))

    subQuery = exportQuery.subquery(name)
    return subQuery


def getAttributes(session, name, split=Split.NAME, prefix=''):
    """
    Consolidates all of the attributes in a form hierarchy into a flat header.
    """
    names = []
    attributes = {}

    schemaCheckQuery = (
        session.query(model.Schema)
        .filter(model.Schema.name == name)
        .filter(model.Schema.publish_date != None)
        )

    count = schemaCheckQuery.count()

    if count <= 0:
        raise InvalidEntitySchemaError(name)

    attributeQuery = (
        session.query(model.Attribute)
        .join(model.Attribute.schema)
        .filter(model.Schema.name == name)
        .filter(model.Schema.publish_date != None)
        .order_by(
            model.Schema.publish_date.asc(),
            model.Attribute.order.asc(),
            )
        )

    for attribute in attributeQuery:
        if attribute.type == 'object':
            subnames, subattributes = getAttributes(
                session=session,
                name=attribute.object_schema.name,
                prefix=attribute.name + '_',
                split=split,
                )

            for subname in subnames:
                if subname not in attributes:
                    names.append(subname)

            attributes.update(subattributes)
        else:
            specialName = prefix + attribute.name

            if split == Split.CHECKSUM:
                specialName += '_' + attribute.checksum

            if specialName not in attributes:
                names.append(specialName)
                attributes.setdefault(specialName, [])

            attributes[specialName].append(attribute)

    return names, attributes


class collection(ColumnElement):
    """
    Collection element for dynamically representing a collection in any
    vendor-specific dialect.
    """

    def __init__(self, column, separator='-', order_by=None):
        self.column = column
        self.separator = separator
        self.order_by = order_by


@compiler.compiles(collection, 'postgres')
@compiler.compiles(collection, 'postgresql')
def compileCollectionPostgreSql(element, compiler, **kw):
    return "ARRAY(%s)" % compiler.process(element.column)


@compiler.compiles(collection, 'sqlite')
def compileCollectionSqlite(element, compiler, **kw):
    return "GROUP_CONCAT(%s)" % compiler.process(element.column)
