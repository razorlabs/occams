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
    Builds a schema entity data report query table from the data dictioanry.

    Arguments
        ``session``
            The database session to use
        ``data_dict``
            The data dictionary that plans out how the final result query
            should be structured.

    Returns
        A SQLAlchemy aliased sub-query. Depending on the database driver,
        the result will either be an aliased subquery or a
        Common Table Expression (or CTE).

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
    report_class = orm.aliased(model.Entity, name=report_name)
    joins = {report_name: report_class}

    # we only want entities of published schemata
    query = (session.query(report_class.id.label('entity_id'))
                .filter(report_class.schema.has(
                        (model.Schema.name == report_name)
                        & (model.Schema.publish_date != None))))

    for column in data_dict.itervalues():
        attributes = column.attributes
        schema_name = attributes[-1].schema.name

        # evaluate the target mapped class and casted value column
        type_ = column.type
        alias_name = type_ + '_' + column.name
        value_class = orm.aliased(storage.nameModelMap[type_], name=alias_name)
        value_column = sa.cast(value_class._value, storage.nameCastMap[type_])

        if 'date' in type_:
            # sqlite sucks at datetimes so we have to fallback functions
            value_column = (getattr(sa.func, type_)(value_class._value)
                            if is_sqlite else value_column)

        if schema_name not in joins:
            # Sub attributes are added via LEFT OUTER JOIN using the object
            # as an association table
            join_name = 'object_' + schema_name
            join_class = orm.aliased(model.ValueObject, name=join_name)
            entity_class = orm.aliased(model.Entity, name=schema_name)
            query = query.outerjoin(join_class, (
                    (report_class.id == join_class.entity_id)
                        & join_class.attribute_id.in_(
                            [a.schema.parent_attribute.id for a in attributes])))
            query = query.outerjoin(entity_class,
                            (entity_class.id == join_class._value))
            joins[schema_name] = entity_class

        entity_class = joins[schema_name]
        filter_expression = (
            (entity_class.id == value_class.entity_id)
            & (value_class.attribute_id.in_([a.id for a in attributes])))

        if reduce(or_, imap(lambda a: bool(a.is_collection), attributes)):
            # Collections are added via correlated sub-queries to the report
            if column.selection is None:
                value_column = collect(
                    session.query(aggregate(value_column))
                    .filter(filter_expression)
                    .correlate(entity_class)
                    .as_scalar())
            else:
                value_column = (
                    session.query(true())
                    .filter(filter_expression)
                    .filter(value_column == column.selection.value)
                    .correlate(entity_class)
                    .as_scalar())
        else:
            # Scalar columns are added via LEFT OUTER JOIN
            query = query.outerjoin(value_class, filter_expression)

        query = query.add_column(value_column.label(column.name))

    return query.subquery(report_name) if is_sqlite else query.cte(report_name)


class DataDict(object):
    u"""
    A representation (or plan) of what a report table will look like.
    Objects of this class can be used as a reference for report table
    output (or generation, see ``buildReportTable``)
    This type also behaves as a dictionary, granting access to data
    columns as key values.
    """

    @property
    def name(self):
        return self.__schema_name

    def __init__(self, schema_name, columns):
        self.__schema_name = schema_name
        self.__columns = copy(columns)

    def __makekey(self, key):
        return  key if isinstance(key, basestring) else '_'.join(map(str, key))

    def get(self, key, default=None):
        if key in self:
            return self[key]
        else:
            return default

    def __getitem__(self, key):
        return self.__columns[self.__makekey(key)]

    def __contains__(self, key):
        return self.__makekey(key) in self.__columns

    def __len__(self):
        return len(self.__columns)

    def items(self):
        return list(self.iteritems())

    def keys(self):
        return list(self.iterkeys())

    def paths(self):
        return list(self.iterpaths())

    def values(self):
        return list(self.itervalues())

    def iteritems(self):
        return self.__columns.iteritems()

    def iterkeys(self):
        return self.__columns.iterkeys()

    def iterpaths(self):
        return imap(lambda c: c.path, self.itervalues())

    def itervalues(self):
        return self.__columns.itervalues()


class DataColumn(object):
    u"""
    A data dictionary column for reference when inspecting a report column.
    This type also behaves as a dictionary, granting access to vocabulary
    terms (if the underlying attributes have specified choices).
    """

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

