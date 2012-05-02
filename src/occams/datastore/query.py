"""
A utility for allowing the access of entered schema data to be represented
in a SQL table-like fashion.
"""

from ordereddict import OrderedDict
from sqlalchemy import cast
from sqlalchemy import func
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


def schemaToSubquery(session, name, split=Split.NAME):
    """
    Returns a schema entity data as an aliased sub-query.

    This query can then be further queried to fulfill bureaucratic requirements.

    Suggested usage of subquery is via "common table expressions" (i.e. WITH staement...)

    Arguments
        ``session``
            The session to query attributes from
        ``name``
            The name of the schema family to generate the subquery for
        ``split``
            (Optional) the splitting algorithm to use. Default is by name.
        ``merge``
            (Optional) a reverse lookup dictionary to how columns should be combined
            Essentially, a dictionary who's key / value pairs are interpreted
            as: "column_name" / "column_to_combine_with"
        ``naming``
            (Optional) The naming scheme to use, default is ``defaultColumnNaming``
            Client applications can override this by passing a method
            callback which will be passed the following parameters:
                * session: session being used
                * name: the schema that the subquery is being generated for
                * split: splitting algorithm used
                * path: the key in the column plan
                * attributes: the attributes for the column
            Note that merge is not passed as a parameter as this method
            takes care of the final column merging.

    Returns
        A tuple containing the plan used, and the final subquery

        Developer note: the results that will be returned by the subquery are
        named tuples of each result using the names of the naming schema as the
        property names.

    """

    # Collapse all the related attributes into an ordered tree
    plan = getColumnPlan(session, name, split)

    exportQuery = (
        session.query(model.Entity.id.label('entity_id'))
        .join(model.Entity.schema)
        .filter((model.Schema.name == name) & (model.Schema.publish_date != None))
        )

    for path, attributes in plan.iteritems():
        columnName = '_'.join(path)
        finalType = attributes[-1].type
        ids = [a.id for a in attributes]
        isEverCollection = True in set([a.is_collection for a in attributes])

        Value = aliased(nameModelMap[finalType], name='%s_%s' % (columnName, finalType))
        valueClause = (Value.entity_id == model.Entity.id) & (Value.attribute_id.in_(ids))
        # SA really doesn't like the hybrid property for casting, use the _column
        valueCasted = convert(Value._value, finalType)

        if isEverCollection:
            # Collections are built using correlated subqueries
            valueQuery = session.query(valueCasted).filter(valueClause)
            column = collection(valueQuery.correlate(model.Entity).as_scalar())
        else:
            # Scalars are build via LEFT JOIN
            exportQuery = exportQuery.outerjoin(Value, valueClause)
            column = valueCasted

        exportQuery = exportQuery.add_column(column.label(columnName))

    subQuery = exportQuery.subquery(name)
    return plan, subQuery


def getColumnPlan(session, name, split=Split.NAME, path=()):
    """
    Consolidates all the plan in a schema hierarchy into a single listing.
    The way this is accomplished is by traversing all the nodes in each
    hierarchy level and reporting only the leaf nodes (i.e. basic data types,
    not sub schemata)

    Note that the final columns are ordered by most recent order number within
    the parent, then by the parent's publication date (oldest to newest).

    Arguments
        ``session``
            The session to query plan from
        ``name``
            The name of the schema to get columns plans for
        ``split``
            (Optional) the splitting algorithm to use. Default is by name.
        ``path``
            (Optional)  current traversing path in the hierarchy.
            This is useful if you want to prepend additional column
            prefixes.

    Returns
        An ordered dictionary using the path to the attribute as the key,
        and the associated attribute list as the value. Depending on
        the splitting method specified, the path will also have
        the attributes' id or checksum as well.

    """
    plan = OrderedDict()

    schemaCheckQuery = (
        session.query(model.Schema)
        .filter((model.Schema.name == name) & (model.Schema.publish_date != None))
        )

    count = schemaCheckQuery.count()

    if count <= 0:
        raise InvalidEntitySchemaError(name)

    # Aliased so we don't get naming ambiguity
    RecentAttribute = aliased(model.Attribute, name='recent_attribute')

    # Build a subquery that determines an attribute's most recent order
    recentOrderSubQuery = (
        session.query(RecentAttribute.order)
        .join(RecentAttribute.schema)
        .filter((model.Schema.name == name) & (model.Schema.publish_date != None))
        .filter(RecentAttribute.name == model.Attribute.name)
        .order_by(model.Schema.publish_date.desc())
        .limit(1)
        .correlate(model.Attribute)
        .as_scalar()
        )

    # Get all the attributes ordered by their most recent order, then oldest to newest
    attributeQuery = (
        session.query(model.Attribute)
        .join(model.Attribute.schema)
        .filter((model.Schema.name == name) & (model.Schema.publish_date != None))
        .order_by(
            recentOrderSubQuery.asc(),
            model.Schema.publish_date.asc(),
            )
        )

    for attribute in attributeQuery:
        if attribute.type == 'object':
            subName = attribute.object_schema.name
            subPath = (attribute.name,)
            subPlan = getColumnPlan(session, subName, split, subPath)
            plan.update(subPlan)
        else:
            if split == Split.CHECKSUM:
                columnPath = path + (attribute.name, attribute.checksum)
            elif split == Split.ID:
                columnPath = path + (attribute.name, attribute.id)
            else:
                columnPath = path + (attribute.name,)
            plan.setdefault(columnPath, []).append(attribute)

    return plan


class convert(ColumnElement):
    """
    Collection element for dynamically representing a collection in any
    vendor-specific dialect.
    """

    def __init__(self, column, typeName):
        self.column = column
        self.typeName = typeName
        self.type = nameCastMap[typeName]


@compiler.compiles(convert, 'sqlite')
def compileConvertSqlite(element, compiler, **kw):
    # Very special case for sqlite as it has limited data types
    if element.typeName == 'date':
        converted = func.date(element.column)
    elif element.typeName == 'datetime':
        converted = func.datetime(element.column)
    else:
        converted = cast(element.column, element.type)
    return compiler.process(converted)


@compiler.compiles(convert, 'postgres')
@compiler.compiles(convert, 'postgresql')
def compileConvertPostgresql(element, compiler, **kw):
    return compiler.process(cast(element.column, element.type))


class collection(ColumnElement):
    """
    Collection element for dynamically representing a collection in any
    vendor-specific dialect.
    """

    def __init__(self, column, separator='-', order_by=None):
        self.column = column
        self.separator = separator
        self.order_by = order_by
        # TODO: needs type


@compiler.compiles(collection, 'postgres')
@compiler.compiles(collection, 'postgresql')
def compileCollectionPostgreSql(element, compiler, **kw):
    return "ARRAY(%s)" % compiler.process(element.column)


@compiler.compiles(collection, 'sqlite')
def compileCollectionSqlite(element, compiler, **kw):
    return "GROUP_CONCAT(%s)" % compiler.process(element.column)
