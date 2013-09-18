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

    ``column plan`` or ``header`` or ``data dict``
        The concept of inspecting a schema's history in order to flatten it
        into an exportable table. A data dict contains information about what
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

    ``grouping``
        Because of the nature of how datastore handles schema versions, this module
        offers different kinds of reporting granularity in the form of
        *attribute grouping*, meaning that the attribute metdata is inpected to
        determine how the final report columns show up in the query. This module
        ships with ID/NAME/CHECKSUM built in, with the ability to specify
        any other grouping algorithm the client wishes.
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


def schemaToReport(session, id_or_name):
    """
    Generates a report for the schema based on the given splitting algorithm

    Arguments:
        ``session``
            The SQLAlchemy session to use
        ``id_or_name``
            The schema's id or (name, publish_date) tuple

    Returns:
        A (``DataDict``, ``Query``) pair.
    """
    data_dict = buildDataDict(session, schema_name)
    table = buildReportTable(session, data_dict)
    return data_dict, table


def buildDataDict(session, id_or_name):
    u"""
    Builds a ``DataDict`` for the schema hierarchy

    The columns reported are only the basic data types.

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
            The grouping algorithm to use, this is a callback that will
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

    attribute_query = (
        session.query(model.Attribute)
        .options(
            orm.joinedload(model.Attribute.schema),
            orm.joinedload(model.Attribute.choices))
        .join(model.Attribute.schema))

    if isinstance(id_or_name, int):
        attribute_query = attribute_query.filter_by(id=id_or_name)
    else:
        (name, publish_date) = id_or_name
        attribute_query = \
            attribute_query.filter_by(name=name, publish_date=publish_date)

    attribute_query = attribute_query.order_by(model.Attribute.order)

    plan = OrderedDict()
    selected = dict()

    for attribute in attribute_query:
        if attribute.is_collection and attribute.choices:
            for choice in attribute.choices:
                # the actual value of the choice is more reliable than
                # the name as the name for choices is simply a token
                column_path =  path + group + (choice.value,)
                plan.setdefault(column_path, []).append(attribute)
                selected[column_path] = choice
        else:
            column_path = path + group
            plan.setdefault(column_path, []).append(attribute)

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
        value_column = value_class._value
        if type_ == 'boolean':
            value_column = sa.cast(value_class._value, sa.Boolean)
        elif type_ == 'date':
            # sqlite handles datetimes weirdly
            value_column = (getattr(sa.func, type_)(value_class._value)
                            if is_sqlite
                            else sa.cast(value_class._value, sa.Date))

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

    Note that this type is intended to be read-only.

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
        u""" The key master """
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

    Note that this type is intended to be read-only.

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
        if selection is not None:
            self.__vocabulary = None
        else:
            consolidated = dict([(c.value, c.title)
                                for a in self.attributes
                                for c in a.choices])
            terms = [SimpleTerm(v, title=t) for v, t in consolidated.items()]
            self.__vocabulary = SimpleVocabulary(terms)

    def __getitem__(self, key):
        try:
            return self.vocabulary.getTerm(key)
        except (LookupError, AttributeError) as e:
            raise KeyError(key)

