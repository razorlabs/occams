"""
A utility for allowing the access of entered schema data to be represented
in a SQL table-like fashion.
"""

from ordereddict import OrderedDict
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


def defaultColumnNaming(session, name, split, path, attributes):
    """
    Implements default naming behavior of subquery columns
    """
    return '_'.join(path)


def schemaToSubquery(session, name, split=Split.NAME, merge=dict(), naming=defaultColumnNaming):
    """
    Returns a schema entity data as an aliased sub-query.

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
        A subquery representation of the schema family.

        Note that the results that will be retured by the subquery are
        named tuples of each result using the names of the naming
        schema as the property names.

    """

    # Collapse all the related attributes into an ordered tree
    plan = getColumnPlan(session, name, split=split)

    # TODO somewhere in here we further collapse the attributes based on a
    # configuration file

    exportQuery = (
        session.query(
            model.Entity.id.label('entity_id'),
            model.Entity.state.label('entity_state'),
            model.Entity.collect_date.label('entity_collect_date'),
            )
        .join(model.Entity.schema)
        .filter((model.Schema.name == name) & (model.Schema.publish_date != None))
        )

    for path, attributes in plan.iteritems():
        for attribute in attributes:
            columnName = defaultColumnNaming(session, name, split, path, attributes)

            # YOU LEFT OFF HERE

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

            exportQuery = exportQuery.add_column(column.label(columnName))

    subQuery = exportQuery.subquery(name)
    return subQuery


def getColumnPlan(session, name, split=Split.NAME):
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
            subattributes = getColumnPlan(session, attribute.object_schema.name, split)
            for path, items in subattributes.iteritems():
                plan[(attribute.name,) + path] = items
        else:
            if split == Split.CHECKSUM:
                path = (attribute.name, attribute.checksum)
            elif split == Split.ID:
                path = (attribute.name, attribute.id)
            else:
                path = (attribute.name,)
            plan.setdefault(path, []).append(attribute)

    return plan


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
