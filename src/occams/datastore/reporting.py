u"""
A utility for allowing the access of entered schema data to be represented
in a SQL table-like fashion.

Because of the nature of how datastore handles schema versions, this module
offers difference kinds of reporting granularity in the form of
*attribute splitting*, meaning that the attribute metdata is inpected to
determine how the final report columns show up in the query.
So far, three types of attribute splitting are available:

    **NAME**
        No splitting should occur, all attributes are grouped by their name
    **CHECKSUM**
        All attribute in a lineage are grouped by their checksum
    **ID**
        Aggressively split by attribute id

"""

import ordereddict

import sqlalchemy as sa
from sqlalchemy import orm

from occams.datastore import model as datastore
from occams.datastore.model import storage


def schemaToReportById(session, schema_name):
    u"""
    Builds a sub-query for a schema using the ID split algorithm
    """
    header = getHeaderById(session, schema_name)
    table = buildReportTable(session, schema_name, header)
    return header, table


def schemaToReportByName(session, schema_name):
    u"""
    Builds a sub-query for a schema using the NAME split algorithm
    """
    header = getHeaderByName(session, schema_name)
    table = buildReportTable(session, schema_name, header)
    return header, table


def schemaToReportByChecksum(session, schema_name):
    u"""
    Builds a sub-query for a schema using the CHECKSUM split algorithm
    """
    header = getHeaderByChecksum(session, schema_name)
    table = buildReportTable(session, schema_name, header)
    return header, table


def buildReportTable(session, schema_name, header):
    u"""
    Builds a schema entity data report table as an aliased sub-query.

    Suggested usage of subquery is via "common table expressions" (i.e. WITH statement...)

    Arguments
        ``session``
            The database session to use
        ``name``
            The schema to use for building the sub-query
        ``header``
            The column plan tha will be used for aligning the data

    Returns
        A SQLAlchemy aliased sub-query.

        Developer note: the results that will be returned by the subquery are
        named tuples of each result using the names of the naming schema as the
        property names.
    """
    # special cases depending on the database vendor
    is_sqlite = u'sqlite' in str(session.bind.url)
    is_postgres = u'postgres' in str(session.bind.url)
    # convenient expression for evaluating a list of boleans
    reduce_or = lambda i: reduce((lambda x, y: x or y), i)

    entity_query = (
        session.query(datastore.Entity.id.label(u'entity_id'))
        .join(datastore.Entity.schema)
        .filter(datastore.Schema.name == schema_name)
        .filter(datastore.Schema.publish_date != None)
        )

    sub_entities = dict()

    for path, attributes in header.iteritems():
        column_name = u'_'.join(path)
        type_name = attributes[-1].type
        attribute_ids = [a.id for a in attributes]
        value_source = storage.nameModelMap[type_name]
        value_name = u'%s_%s' % (column_name, type_name)
        value_class = orm.aliased(value_source, name=value_name)
        attribute_clause = (value_class.attribute_id.in_(attribute_ids))
        entity_clause = (value_class.entity_id == datastore.Entity.id)
        value_clause = entity_clause & attribute_clause
        # sqlalchemy doesn't like the hybrid property for casting
        value_column = value_class._value
        is_ever_collection = reduce_or([a.is_collection for a in attributes])
        is_ever_subattribute = reduce_or([a.schema.is_inline for a in attributes])

        # very special case for sqlite as it has limited data type
        if is_sqlite and type_name == u'date':
            value_casted = sa.func.date(value_column)
        elif is_sqlite and type_name == u'datetime':
            value_casted = sa.func.datetime(value_column)
        else:
            value_casted = sa.cast(value_column, storage.nameCastMap[type_name])

        if is_ever_collection:
            # collections are built using correlated subqueries
            if is_postgres:
                # use postgres arrays if available
                aggregator = sa.func.array
                aggregate_values = value_casted
            else:
                # everything else get's a comma-delimeted string
                aggregator = lambda q: q
                aggregate_values = sa.func.group_concat(value_casted)

            column_part = aggregator(
                session.query(aggregate_values)
                .filter(value_clause)
                .correlate(datastore.Entity)
                .as_scalar()
                )
        elif is_ever_subattribute:
            # need to do an extra left join for the sub-object assocation table
            associate_name = path[0]

            if associate_name not in sub_entities:
                associate_class = orm.aliased(datastore.ValueObject, name=associate_name)
                associate_clause = (datastore.Entity.id == associate_class.entity_id)
                entity_query = entity_query.outerjoin(associate_class, associate_clause)
            else:
                associate_class = sub_entities[associate_name]

            entity_clause =  (value_class.entity_id == associate_class._value)
            # override the value_clause to use the object association table
            value_clause = entity_clause & attribute_clause
            entity_query = entity_query.outerjoin(value_class, value_clause)
            column_part = value_casted
        else:
            # scalars are build via LEFT JOIN
            entity_query = entity_query.outerjoin(value_class, value_clause)
            column_part = value_casted

        entity_query = entity_query.add_column(column_part.label(column_name))

    if is_sqlite:
        # sqlite does not support common table expressions
        report_table = entity_query.subquery(schema_name)
    else:
        report_table = entity_query.cte(schema_name)

    return report_table


def getHeaderByName(session, schema_name, path=()):
    u"""
    Builds a column header for the schema hierarchy using the NAME algorithm.
    The header columns reported are only the basic data types.

    Note that the final columns are ordered by most recent order number within
    the parent, then by the parent's publication date (oldest to newest).

    Arguments
        ``session``
            The session to query plan from
        ``name``
            The name of the schema to get columns plans for
        ``path``
            (Optional)  current traversing path in the hierarchy.
            This is useful if you want to prepend additional column
            prefixes.

    Returns
        An ordered dictionary using the path to the attribute as the key,
        and the associated attribute list as the value.
    """
    plan = ordereddict.OrderedDict()
    attribute_query = getAttributeQuery(session, schema_name)
    for attribute in attribute_query:
        if attribute.type == u'object':
            sub_name = attribute.object_schema.name
            sub_path = (attribute.name,)
            sub_plan = getHeaderByName(session, sub_name, sub_path)
            plan.update(sub_plan)
        else:
            column_path = path + (attribute.name,)
            plan.setdefault(column_path, []).append(attribute)
    return plan


def getHeaderByChecksum(session, schema_name, path=()):
    u"""
    Builds a column header for the schema hierarchy using the CHECKSUM algorithm.
    The header columns reported are only the basic data types.

    Note that the final columns are ordered by most recent order number within
    the parent, then by the parent's publication date (oldest to newest).

    Arguments
        ``session``
            The session to query plan from
        ``name``
            The name of the schema to get columns plans for
        ``path``
            (Optional)  current traversing path in the hierarchy.
            This is useful if you want to prepend additional column
            prefixes.

    Returns
        An ordered dictionary using the path to the attribute as the key,
        and the associated attribute list as the value. The path will
        also contain the attribute's checksum.
    """
    plan = ordereddict.OrderedDict()
    attribute_query = getAttributeQuery(session, schema_name)
    for attribute in attribute_query:
        if attribute.type == u'object':
            sub_name = attribute.object_schema.name
            sub_path = (attribute.name,)
            sub_plan = getHeaderByChecksum(session, sub_name, sub_path)
            plan.update(sub_plan)
        else:
            column_path = path + (attribute.name, attribute.checksum)
            plan.setdefault(column_path, []).append(attribute)
    return plan


def getHeaderById(session, schema_name, path=()):
    u"""
    Builds a column header for the schema hierarchy using the ID algorithm.
    The header columns reported are only the basic data types.

    Note that the final columns are ordered by most recent order number within
    the parent, then by the parent's publication date (oldest to newest).

    Arguments
        ``session``
            The session to query plan from
        ``name``
            The name of the schema to get columns plans for
        ``path``
            (Optional)  current traversing path in the hierarchy.
            This is useful if you want to prepend additional column
            prefixes.

    Returns
        An ordered dictionary using the path to the attribute as the key,
        and the associated attribute list as the value. The path will
        also contain the attribute's id.
    """
    plan = ordereddict.OrderedDict()
    attribute_query = getAttributeQuery(session, schema_name)
    for attribute in attribute_query:
        if attribute.type == u'object':
            sub_name = attribute.object_schema.name
            sub_path = (attribute.name,)
            sub_plan = getHeaderById(session, sub_name, sub_path)
            plan.update(sub_plan)
        else:
            column_path = path + (attribute.name, attribute.id)
            plan.setdefault(column_path, []).append(attribute)
    return plan


def getAttributeQuery(session, schema_name):
    u"""
    Builds a subquery for the all attributes ever contained in the schema.
    This does not include sub-attributes.

    Arguments:
        ``session``
            The SQLAlchemy session to use
        ``schema_name``
            The schema to search for in the session

    Returns:
        A subquery for all the attributes every contained in the schema.
        Attribute lineages are are ordered by their most recent position in the
        schema, then by oldest to newest within the lineage.
    """

    # aliased so we don't get naming ambiguity
    RecentAttribute = orm.aliased(datastore.Attribute, name=u'recent_attribute')

    # build a subquery that determines an attribute's most recent order
    recent_order_subquery = (
        session.query(RecentAttribute.order)
        .join(RecentAttribute.schema)
        .filter(datastore.Schema.name == schema_name)
        .filter(datastore.Schema.publish_date != None)
        .filter(RecentAttribute.name == datastore.Attribute.name)
        .order_by(datastore.Schema.publish_date.desc())
        .limit(1)
        .correlate(datastore.Attribute)
        .as_scalar()
        )

    attribute_query = (
        session.query(datastore.Attribute)
        .options(
            orm.joinedload(datastore.Attribute.schema),
            orm.joinedload(datastore.Attribute.choices),
            )
        .join(datastore.Attribute.schema)
        .filter(datastore.Schema.name == schema_name)
        .filter(datastore.Schema.publish_date != None)
        .order_by(
            # lineage order
            recent_order_subquery.asc(),
            # oldest to newest within the lineage
            datastore.Schema.publish_date.asc(),
            )
        )

    return attribute_query

