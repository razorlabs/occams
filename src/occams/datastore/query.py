"""
A utility for allowing the access of entered schema data to be represented
in a SQL table-like fashion.
"""

from ordereddict import OrderedDict
from sqlalchemy import cast
from sqlalchemy import func
from sqlalchemy.orm import aliased
from sqlalchemy.orm import joinedload

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

        Value = aliased(nameModelMap[finalType], name='%s_%s' % (columnName, finalType))
        valueClause = (Value.entity_id == model.Entity.id) & (Value.attribute_id.in_(ids))

        # SA really doesn't like the hybrid property for casting, use the _column
        rawColumn = Value._value

        # Very special case for sqlite as it has limited data types
        if 'sqlite' in str(session.bind.url) and finalType in ('date', 'datetime'):
            if finalType == 'date':
                valueCasted = func.date(rawColumn)
            elif finalType == 'datetime':
                valueCasted = func.datetime(rawColumn)
        else:
            valueCasted = cast(rawColumn, nameCastMap[finalType])

        # Hanlde collections
        if True in set([a.is_collection for a in attributes]):
            # Collections are built using correlated subqueries
            if 'postgresql' in str(session.bind.url):
                # Special logic for postrgres, because it supports actual arrays
                column = func.array(
                    session.query(valueCasted)
                    .filter(valueClause)
                    .correlate(model.Entity)
                    .subquery()
                    )
            else:
                # Everything else get's a comma-delimeted string
                column = (
                    session.query(func.group_concat(valueCasted))
                    .filter(valueClause)
                    .correlate(model.Entity)
                    .subquery()
                    )

        # Handle sub objects
        elif True in set([a.schema.is_inline for a in attributes]):
            pass

        # Handle scalar values
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
        .options(
            joinedload(model.Attribute.schema),
            joinedload(model.Attribute.choices),
            )
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
