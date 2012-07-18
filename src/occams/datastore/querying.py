u"""
A utility for allowing the access of entered schema data to be represented
in a SQL table-like fashion.

Splitting algorithms are as follows:
    ``NAME``
        No splitting should occur, all attributes are grouped by their name
    ``CHECKSUM``
        All attributes are grouped by their checksum
    ``ID``
        Aggressively split by attribute id

"""

import ordereddict

import sqlalchemy as sa
from sqlalchemy import orm

from occams.datastore import model as datastore
from occams.datastore.model import storage


BY_NAME, BY_CHECKSUM, BY_ID = range(3)


def schemaToSubquery(session, name, split=BY_NAME):
    u"""
    Returns a schema entity data as an orm.aliased sub-query.

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
        session.query(datastore.Entity.id.label(u'entity_id'))
        .join(datastore.Entity.schema)
        .filter((datastore.Schema.name == name) & (datastore.Schema.publish_date != None))
        )

    for path, attributes in plan.iteritems():
        columnName = u'_'.join(path)
        finalType = attributes[-1].type
        ids = [a.id for a in attributes]

        Value = orm.aliased(storage.nameModelMap[finalType], name=u'%s_%s' % (columnName, finalType))
        valueClause = (Value.entity_id == datastore.Entity.id) & (Value.attribute_id.in_(ids))

        # SA really doesn't like the hybrid property for casting, use the _column
        rawColumn = Value._value

        # Very special case for sqlite as it has limited data types
        if u'sqlite' in str(session.bind.url) and finalType in (u'date', u'datetime'):
            if finalType == u'date':
                valueCasted = sa.func.date(rawColumn)
            elif finalType == u'datetime':
                valueCasted = sa.func.datetime(rawColumn)
        else:
            valueCasted = sa.cast(rawColumn, storage.nameCastMap[finalType])

        # Hanlde collections
        if True in set([a.is_collection for a in attributes]):
            # Collections are built using correlated subqueries
            if u'postgresql' in str(session.bind.url):
                # Special logic for postrgres, because it supports actual arrays
                column = sa.func.array(
                    session.query(valueCasted)
                    .filter(valueClause)
                    .correlate(datastore.Entity)
                    .subquery()
                    )
            else:
                # Everything else get's a comma-delimeted string
                column = (
                    session.query(sa.func.group_concat(valueCasted))
                    .filter(valueClause)
                    .correlate(datastore.Entity)
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


def getColumnPlan(session, name, split=BY_NAME, path=()):
    u"""
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
    plan = ordereddict.OrderedDict()

    # orm.aliased so we don't get naming ambiguity
    RecentAttribute = orm.aliased(datastore.Attribute, name=u'recent_attribute')

    # Build a subquery that determines an attribute's most recent order
    recentOrderSubQuery = (
        session.query(RecentAttribute.order)
        .join(RecentAttribute.schema)
        .filter((datastore.Schema.name == name) & (datastore.Schema.publish_date != None))
        .filter(RecentAttribute.name == datastore.Attribute.name)
        .order_by(datastore.Schema.publish_date.desc())
        .limit(1)
        .correlate(datastore.Attribute)
        .as_scalar()
        )

    # Get all the attributes ordered by their most recent order, then oldest to newest
    attributeQuery = (
        session.query(datastore.Attribute)
        .options(
            orm.joinedload(datastore.Attribute.schema),
            orm.joinedload(datastore.Attribute.choices),
            )
        .join(datastore.Attribute.schema)
        .filter((datastore.Schema.name == name) & (datastore.Schema.publish_date != None))
        .order_by(
            recentOrderSubQuery.asc(),
            datastore.Schema.publish_date.asc(),
            )
        )

    for attribute in attributeQuery:
        if attribute.type == u'object':
            subName = attribute.object_schema.name
            subPath = (attribute.name,)
            subPlan = getColumnPlan(session, subName, split, subPath)
            plan.update(subPlan)
        else:
            if split == BY_CHECKSUM:
                columnPath = path + (attribute.name, attribute.checksum)
            elif split == BY_ID:
                columnPath = path + (attribute.name, attribute.id)
            else:
                columnPath = path + (attribute.name,)
            plan.setdefault(columnPath, []).append(attribute)

    return plan

