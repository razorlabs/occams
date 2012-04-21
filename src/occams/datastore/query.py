"""
A utility for allowing the access of entered schema data to be represented
in a SQL table-like fashion.

Steps to build:
    * Collapse all the related attributes into an ordered tree
    * The tree will then be used as the header
    * Use a configuration file to further condense the header plan
    * with the header we can then begin building a subquery for the actual data
"""

from sqlalchemy import cast
from sqlalchemy.ext import compiler
from sqlalchemy.sql import ColumnElement
from sqlalchemy.orm import aliased

from occams.datastore import model
from occams.datastore.model.storage import nameCastMap
from occams.datastore.model.storage import nameModelMap


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

    names, columns = getHeader(session, name, split=False)

    for name in names:
        print name

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

#    for attribute in attributeQuery:
#        Value = aliased(nameModelMap[attribute.type])
#
#        if attribute.is_collection:
#            column = collection(
#                session.query(cast(Value._value, nameCastMap[attribute.type]))
#                .filter(Value.entity_id == model.Entity.id)
#                .filter(Value.attribute_id == attribute.id)
#                .correlate(model.Entity)
#                .subquery()
#                .as_scalar()
#                )
#        else:
#            exportQuery = exportQuery.outerjoin(
#                Value,
#                ((Value.entity_id == model.Entity.id) &
#                    (Value.attribute_id == attribute.id))
#                )
#
#            column = cast(Value._value, nameCastMap[attribute.type])
#
#        exportQuery = exportQuery.add_column(column.label(attribute.name))

    subQuery = exportQuery.subquery(name)
    return subQuery


def getHeader(session, name, split=False, prefix=''):
    names = []
    columns = {}

    attributeQuery = (
        session.query(model.Attribute)
        .join(model.Attribute.schema)
        .filter(model.Schema.name == name)
        .filter(model.Schema.publish_date != None)
        .order_by(
            model.Attribute.order.asc(),
            model.Schema.publish_date.asc()
            )
        )

    for attribute in attributeQuery:
        if attribute.type == 'object':
            subnames, subcolumns = getHeader(
                session=session,
                name=attribute.object_schema.name,
                prefix=attribute.name + '_',
                split=split,
                )
            names.extend(subnames)
            columns.update(subcolumns)
        else:
            specialName = attribute.name

            if split:
                specialName += '_' + attribute.checksum

            if specialName not in columns:
                names.append(specialName)
                columns.setdefault(specialName, [])

            columns[specialName].append(attribute)

    return names, columns


class collection(ColumnElement):
    def __init__(self, column, separator='-', order_by=None):
        self.column = column
        self.separator = '-'
        self.order_by = order_by


@compiler.compiles(collection, 'postgres')
@compiler.compiles(collection, 'postgresql')
def compileCollectionPostgreSql(element, compiler, **kw):
    return "ARRAY(%s)" % compiler.process(element.column)
