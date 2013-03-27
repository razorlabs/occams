u"""
A utility for allowing the access of entered schema data to be represented
in a SQL table-like fashion.

Some key terms to keep in mind for this documentation:

    ``lineage`` or ``ancestry``
        For a given attribute name, all the *published* attributes that
        have every existed.

    ``hiearchy`` or ``path``
        The attributes location in the schema
        (e.q. Form -> attribute -> sub-attribute)

    ``column plan`` or ``header``
        Thee concept of inspect a schema's history in order to flatten it
        into an exportable table. A plan contains information about what
        information each column in the report should contain and how to
        render it (e.g. types/objects/collections)

    ``report`` or ``export``
        The actual exported entity, flattened by a column plan. The goal
        of the report is to consolidate all the EAV data for an entity into
        a queryable result, so that it can then be further queried as if it
        an actual table. Therefore, depending on the database vendor, the
        final report will either be a common-table-expression (CTE) result
        or just a subquery. Usage of a vendor that supports CTE is strongly
        encouraged, especially when joining different reports (which
        the subquery result doesn't handle very well)

Because of the nature of how model.handles schema versions, this module
offers difference kinds of reporting granularity in the form of
*attribute splitting*, meaning that the attribute metdata is inpected to
determine how the final report columns show up in the query.
"""

from itertools import imap
from ordereddict import OrderedDict
from operator import or_
from copy import copy

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.sql.expression import true, exists, bindparam
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm

from . import model
from .model import storage


def schemaToReportById(session, schema_name, expand_choice=False):
    u"""
    Builds a sub-query for a schema using the ID split algorithm
    ID Algorithm: Aggressively split by attribute id
    """
    groupfunc = lambda a: (a.name, a.id)
    return schemaToReport(session, schema_name, groupfunc, expand_choice)


def schemaToReportByName(session, schema_name, expand_choice=False):
    u"""
    Builds a sub-query for a schema using the NAME split algorithm
    NAME: All attribute in a lineage are grouped by their checksum
    """
    groupfunc = lambda a: (a.name,)
    return schemaToReport(session, schema_name, groupfunc, expand_choice)


def schemaToReportByChecksum(session, schema_name, expand_choice=False):
    u"""
    Builds a sub-query for a schema using the CHECKSUM split algorithm
    CHECKSUM
    """
    groupfunc = lambda a: (a.name, a.checksum)
    return schemaToReport(session, schema_name, groupfunc, expand_choice)


def schemaToReport(session, schema_name, groupfunc, expand_choice=False):
    u"""
    Generates a report for the schema based on the given splitting algorithm

    Arguments:
        ``session``
            The SQLAlchemy session to use
        ``schema_name``
            The schema to search for in the session
        ``groupfunc``
            The grouping algorithm to use. This method is a callback that
            takes  an attribute as a parameter and returns a tuple
            that will be used to "group" attributes that return the
            same tuple. Results may vary.
        ``expand_choice``
            (Optional) Also expands multiple choice attributes into
            individual "flag" boolean columns.

    Returns:
        A (``DataDict``, ``Query``) pair.
    """
    data_dict = buildDataDict(session, schema_name, groupfunc, expand_choice)
    table = buildReportTable(session, data_dict)
    return data_dict, table


def queryAttributes(session, schema_name):
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
    RecentAttribute = orm.aliased(model.Attribute, name=u'recent_attribute')

    attribute_query = (
        session.query(model.Attribute)
        .options(
            orm.joinedload(model.Attribute.schema),
            orm.joinedload(model.Attribute.choices))
        .join(model.Attribute.schema)
        .filter(model.Schema.name == bindparam('schema_name'))
        .filter(model.Schema.publish_date != None)
        .order_by(
            # determines an attribute's most recent order
            (session.query(RecentAttribute.order)
                .join(RecentAttribute.schema)
                .filter(model.Schema.name == bindparam('schema_name'))
                .filter(model.Schema.publish_date != None)
                .filter(RecentAttribute.name == model.Attribute.name)
                .order_by(model.Schema.publish_date.desc())
                .limit(1)
                .correlate(model.Attribute)
                .as_scalar()).asc(),
            # oldest to newest within the lineage
            model.Schema.publish_date.asc()))
    return attribute_query.params(schema_name=schema_name)


def buildDataDict(session, schema_name, groupfunc, expand_choice=False):
    u"""
    Builds a column header for the schema hierarchy.
    The header columns reported are only the basic data types.

    Note that the final columns are ordered by most recent order number within
    the parent, then by the parent's publication date (oldest to newest).

    Attribute lineages are are ordered by their most recent position in the
    schema, then by oldest to newest within the lineage.

    Arguments
        ``session``
            The session to query plan from
        ``schema_name``
            The name of the schema to get columns plans for
        ``groupfunc``
            The splitting algorithm to use, this is a callback that will
            return a tuple based on the passed attribute. The tuple should
            specific the group that the attribute value belongs in.
        ``expand_choice``
            (Optional) Also expands multiple choice attributes into
            individual "flag" boolean columns.

    Returns
        An ordered dictionary using the path to the attribute as the key,
        and the associated attribute list as the value. The path will
        also contain the attribute's checksum.
    """
    def inspect(current_schema, path=()):
        plan = OrderedDict()
        selected = dict()
        for attribute in queryAttributes(session, current_schema):
            if attribute.type == u'object':
                subschema_name = attribute.object_schema.name
                subschema_path = (attribute.name,)
                subplan, subselected = inspect(subschema_name, subschema_path)
                plan.update(subplan)
                selected.update(subselected)
            else:
                group = groupfunc(attribute)
                if (expand_choice
                        and attribute.is_collection
                        and attribute.choices):
                    for choice in attribute.choices:
                        # the actual value of the choice is more reliable than
                        # the name as the name for choices is simply a token
                        column_path =  path + group + (choice.value,)
                        plan.setdefault(column_path, []).append(attribute)
                        selected[column_path] = choice
                else:
                    column_path = path + group
                    plan.setdefault(column_path, []).append(attribute)
        return plan, selected

    plan, selected = inspect(schema_name)
    columns = OrderedDict()
    for path, attributes in plan.iteritems():
        data_column = DataColumn(path, attributes, selected.get(path))
        columns[data_column.name]  = data_column

    return  DataDict(schema_name, columns)


def buildReportTable(session, data_dict):
    u"""
    Builds a schema entity data report table as an aliased sub-query.

    Suggested usage of subquery is via "common table expressions" (i.e. WITH statement...)

    Arguments
        ``session``
            The database session to use
        ``schema_name``
            The schema to use for building the sub-query
        ``header``
            The column plan tha will be used for aligning the data

    Returns
        A SQLAlchemy aliased sub-query.

        Developer note: the results that will be returned by the subquery are
        named tuples of each result using the names of the naming schema as the
        property names.
    """
    is_sqlite = 'sqlite' == session.bind.url.drivername
    is_postgres = 'postgres' in session.bind.url.drivername

    # native array helper expressions
    collect = lambda q: q if not is_postgres else sa.func.array(q)
    aggregate = lambda c: c if is_postgres else sa.func.group_concat(c)

    # keep track of the subentity joins so we can join subattribute values
    report_name = data_dict.name
    joins = {report_name: model.Entity}

    query = (
        session.query(model.Entity.id.label(u'entity_id'))
        .join(model.Entity.schema)
        .filter(model.Schema.name == report_name)
        .filter(model.Schema.publish_date != None))

    for column in data_dict.itervalues():
        attributes = column.attributes
        schema_name = attributes[-1].schema.name

        # evaluate the target mapped class and cast value column
        type_ = attributes[-1].type
        alias_name = u'_'.join(column.path + (type_,))
        value_class = orm.aliased(storage.nameModelMap[type_], name=alias_name)
        value_casted = sa.cast(value_class._value, storage.nameCastMap[type_])

        if 'date' in type_:
            # sqlite doesn't have very good support of dates
            value_casted = value_casted if not is_sqlite else getattr(sa.func, type_)(value_class._value)

        if schema_name not in joins:
            # need to do an extra left join for the sub-object assocation table
            join_class = orm.aliased(model.ValueObject, name=schema_name + '_join')
            entity_class = orm.aliased(model.Entity, name=schema_name)
            # do a single join to the sub-object
            query = query.outerjoin(join_class, (
                    (model.Entity.id == join_class.entity_id)
                        & join_class.attribute_id.in_(
                            [a.schema.parent_attribute.id for a in attributes])))
            query = query.outerjoin(entity_class, entity_class.id == join_class._value)
            joins[schema_name] = entity_class

        entity_class = joins[schema_name]
        filter_expression = (
            (value_class.entity_id == entity_class.id)
            & (value_class.attribute_id.in_([a.id for a in attributes])))

        if reduce(or_, imap(lambda a: bool(a.is_collection), attributes)):
            if column.selection is None:
                column_part = collect(
                    session.query(aggregate(value_casted))
                    .filter(filter_expression)
                    .correlate(entity_class)
                    .as_scalar())
            else:
                column_part = (
                    session.query(true())
                    .filter(filter_expression & (value_casted == column.selection.value))
                    .correlate(entity_class)
                    .as_scalar())
        else:
            column_part = value_casted
            query = query.outerjoin(value_class, filter_expression)

        query = query.add_column(column_part.label(column.name))

    return query.subquery(report_name) if is_sqlite else query.cte(report_name)


class DataDict(object):

    @property
    def name(self):
        return self.__schema_name

    def __init__(self, schema_name, columns):
        self.__schema_name = schema_name
        self.__columns = copy(columns)

    def get(self, name, default=None):
        return self.__columns.get(name, default)

    def __getitem__(self, key, default=None):
        if not isinstance(key, basestring):
            key = '_'.join(map(str, key))
        return self.__columns[key]

    def __contains__(self, key):
        return key in self.__columns

    def __len__(self):
        return len(self.__columns)

    def items(self):
        return self.__columns.items()

    def keys(self):
        return self.__columns.keys()

    def paths(self):
        return [c.path for c in self.__columns.itervalues()]

    def values(self):
        return self.__columns.values()

    def iteritems(self):
        return self.__columns.iteritems()

    def iterkeys(self):
        return self.__columns.iterkeys()

    def iterpaths(self):
        return imap(lambda c: c.path, self.__columns.itervalues())

    def itervalues(self):
        return self.__columns.itervalues()


class DataColumn(object):

    @property
    def name(self):
        return self.__name

    @property
    def path(self):
        return self.__path

    @property
    def attributes(self):
        return self.__attributes

    @property
    def selection(self):
        return self.__selection

    @property
    def vocabulary(self):
        return  self.__vocabulary

    @property
    def type(self):
        return self.__type

    @property
    def is_nested(self):
        return self.__is_nested

    def __init__(self, path, attributes, selection=None):
        self.__name = '_'.join(map(str, path))
        self.__path = tuple(path)
        self.__type = attributes[-1].type
        self.__attributes = tuple(attributes)
        self.__is_nested = attributes[-1].schema.parent_attribute is not None
        self.__selection = selection
        if selection is None:
            self.__vocabulary = None
        else:
            self.__vocabulary = SimpleVocabulary([SimpleTerm(c.value, title=c.title)
                                                    for a in self.attributes
                                                    for c in a.choices])

    def __getitem__(self, key):
        if self.vocabulary:
            return self.vocabulary.getTerm(key)
        raise KeyError(key)


def _addObject(entity_query, data_column, joined):
    u"""
    Helper method to add object column to the entity query

    Object sub-attributes are added via a LEFT OUTER JOIN to the object
    value table (only once if using the ``joined`` parameter) and then via
    another LEFT OUTER JOIN for each sub-attribute

    This method attempts to join the object value table only once so
    that sub attributes can then join from it. This is of course assuming
    that the calling method is passing the same lookup table reference.

    Arguments
        ``entity_query``
            The pending query being generated
        ``path``
            The column plan path
        ``attributes``
            The attributes in the ancestry for the the path
        ``joined``
            (optional) a lookup table fo joined entities for sub-objects.
            Useful for limitting object table joins to one-per-subobject
            as opposed to one-per-subattribute

    Returns
        The modified entity_query
    """
    path = data_column.path
    attributes = data_column.attributes
    value_class, value_column = _getValueColumn(data_column)

    # we're going to use this as a key in the lookup table of joined objects
    parent_name = attributes[-1].schema.name

    if parent_name not in joined:
        # need to do an extra left join for the sub-object assocation table
        associate_class = orm.aliased(model.ValueObject, name=parent_name)
        # do a single join to the sub-object
        entity_query = entity_query.outerjoin(associate_class, (
            (model.Entity.id == associate_class.entity_id)
            & associate_class.attribute_id.in_(
                [a.schema.parent_attribute.id for a in attributes]
                )
            ))
        # keep a reference in the lookup table
        joined[parent_name] = associate_class

    associate_class = joined[parent_name]

    # each subsequent join should be using the lookup table
    entity_query = entity_query.outerjoin(value_class, (
        (value_class.entity_id == associate_class._value)
        & value_class.attribute_id.in_([a.id for a in attributes])
        ))

    column_part = value_column.label(data_column.name)
    entity_query = entity_query.add_column(column_part)
    return entity_query


def _addCollection(entity_query, data_column, joined):
    u"""
    Helper method to add collection column to the entity query

    Collection attributes are added via correlated sub-queries to the parent
    entity.

    Attempts to use postgres' native array support, otherwise the column is
    generated as a comma-delimited string column.

    Arguments
        ``entity_query``
            The pending query being generated
        ``path``
            The column plan path
        ``attributes``
            The attributes in the ancestry for the the path

    Returns
        The modified entity_query
    """
    session = entity_query.session
    attributes = data_column.attributes
    path = data_column.path
    value_class, value_column = _getValueColumn(data_column)
    is_postgres = 'postgres' in session.bind.url.drivername
    entity_class = joined[attributes[-1].schema.name]

    # uses native arrays if possible
    collect = lambda q: q if not is_postgres else sa.func.array(q)

    # falls back to group concatenation if no native array is available
    aggregate = lambda c: c if is_postgres else sa.func.group_concat(c)

    if data_column.selection is None:
        column_part = collect(
            session.query(aggregate(value_column))
            .filter(value_class.entity_id == entity_class.id)
            .filter(value_class.attribute_id.in_([a.id for a in attributes]))
            .correlate(entity_class)
            .as_scalar())
    else:
        column_part = (
            session.query(true())
            .filter(value_class.entity_id == entity_class.id)
            .filter(value_class.attribute_id.in_([a.id for a in attributes]))
            .filter(value_class._value == data_column.selection.value)
            .correlate(entity_class)
            .as_scalar())

    column_part = column_part.label(data_column.name)
    entity_query = entity_query.add_column(column_part)

    return entity_query


def _addScalar(entity_query, data_column, joined):
    u"""
    Helper method to add scalar column to the entity query
    Scalar columns are added via LEFT OUTER JOIN

    Arguments
        ``entity_query``
            The pending query being generated
        ``path``
            The column plan path
        ``attributes``
            The attributes in the ancestry for the the path

    Returns
        The modified entity_query
    """
    attributes = data_column.attributes
    entity_class = joined[attributes[-1].schema.name]
    value_class, value_column = _getValueColumn(data_column)
    entity_query = entity_query.outerjoin(value_class, (
        (value_class.entity_id == entity_class.id.id)
        & value_class.attribute_id.in_([a.id for a in attributes])
        ))
    column_part = value_column.label(data_column.name)
    entity_query = entity_query.add_column(column_part)
    return entity_query


def _getValueColumn(data_column):
    u"""
    Determines the value class and column for the attributes.

    Arguments
        ``data_column``
            The data dictionary column

    Returns
        A tuple consisting of the value_class to query from as well
        as the casted column containing the actual stored value.
    """
    path = data_column.path
    attributes = data_column.attributes

    session = orm.object_session(attributes[-1])
    is_sqlite = session.bind.url.drivername == 'sqlite'

    # find the correct value class and alias it (for mulitple joins)
    type_name = attributes[-1].type
    source_class = storage.nameModelMap[type_name]
    cast_type = storage.nameCastMap[type_name]
    alias_name = u'_'.join(path + (type_name,))
    value_class = orm.aliased(source_class, name=alias_name)
    value_column = sa.cast(value_class._value, cast_type)

    if 'date' in type_name:
       # sqlite is very finicky about dates: must be function result
       value_column = value_column if not is_sqlite else getattr(sa.func, type_name)

    return value_class, value_column

