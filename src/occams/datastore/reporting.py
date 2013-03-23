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
So far, three types of attribute splitting are available:

    **NAME**
    **CHECKSUM**
    **ID**

"""

from ordereddict import OrderedDict
from operator import or_

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
        A ``data_dict`` and ``Query`` pair.
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
            # lineage order
            # build a subquery that determines an attribute's most recent order
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
    data_dict = DataDict(schema_name)

    def populateFrom(current_schema, path=()):
        for attribute in queryAttributes(session, current_schema):
            if attribute.type == u'object':
                populateFrom(attribute.object_schema.name, (attribute.name,))
            else:
                group = groupfunc(attribute)
                if expand_choice and attribute.is_collection and attribute.choices:
                    for choice in attribute.choices:
                        column_path = path + (choice.value,) + group
                        data_dict.add(column_path, attribute, choice)
                else:
                    column_path = path + group
                    data_dict.add(column_path, attribute)

    populateFrom(schema_name)
    map(lambda dc: dc.updateVocabulary(), data_dict.itervalues())

    return data_dict


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
    # helper expressions
    is_sqlite = session.bind.url.drivername == 'sqlite'
    is_collection =  lambda xs: reduce(or_, [bool(a.is_collection) for a in xs])
    is_object = lambda xs: reduce(or_, [bool(a.schema.is_inline) for a in xs])
    subquery = lambda q, n: q.subquery(n) if is_sqlite else q.cte(n)

    # sub objects that have been joined so we don't rejoin
    joined = dict()
    schema_name = data_dict.name

    entity_query = (
        session.query(model.Entity.id.label(u'entity_id'))
        .join(model.Entity.schema)
        .filter(model.Schema.name == schema_name)
        .filter(model.Schema.publish_date != None))

    for data_column in data_dict.itervalues():
        if is_collection(data_column.attributes):
            entity_query = _addCollection(entity_query, data_column)
        elif is_object(data_column.attributes):
            entity_query = _addObject(entity_query, data_column, joined)
        else:
            entity_query = _addScalar(entity_query, data_column)

    return subquery(entity_query, schema_name)


class DataDict(object):

    @property
    def name(self):
        return self.__schema_name

    @property
    def columns(self):
        return self.__columns

    def __init__(self, schema_name):
        self.__schema_name = schema_name
        self.__columns = OrderedDict()
        self.__schemata = []

    def get(self, name, default=None):
        return self.columns.get(name, default)

    def add(self, path, attributes, selection=None):
        if not isinstance(attributes, list):
            attributes = [attributes]
        column_name = '_'.join(path)
        column = self.columns.get(column_name)
        if column is None:
            column = DataColumn(self, column_name, path)
            self.columns[column_name] = column
        column.selection = selection
        column.attributes.extend(attributes)

    def __getitem__(self, key, default=None):
        if isinstance(key, list):
            key = '_'.join(key)
        return self.columns[key]

    def __contains__(self, key):
        return key in self.columns

    def __len__(self):
        return len(self.columns)

    def items(self):
        return self.columns.items()

    def keys(self):
        return self.columns.keys()

    def paths(self):
        return [c.path for c in self.columns.itervalues()]

    def values(self):
        return self.columns.value()

    def iteritems(self):
        return self.columns.iteritems()

    def iterkeys(self):
        return self.columns.iterkeys()

    def itervalues(self):
        return self.columns.itervalues()

    def iterpaths(self):
        for c in self.columns.itervalues():
            yield c.path


class DataColumn(object):

    @property
    def data_dict(self):
        return self.__data_dict

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

    @selection.setter
    def selection(self, value):
        self.__selection = value

    @property
    def vocabulary(self):
        return  self.__vocabulary

    @property
    def type(self):
        if self.attribtues:
            return self.attributes[-1].type

    @property
    def is_nested(self):
        if self.attributes:
            subschema_name = self.attributes[-1].schema.name
            schema_name = self.data_dict.schemata[-1].name
            return subschema_name == schema_name

    def __init__(self, data_dict, name, path):
        self.__data_dict = data_dict
        self.__name = name
        self.__path = path
        self.__attributes = []
        self.__vocabulary = None

    def updateVocabulary(self):
        self.__vocabulary =  SimpleVocabulary([SimpleTerm(c.value, title=c.title)
                                                for a in self.attributes
                                                for c in a.choices])

    def __getitem__(self, key):
        if self.vocabulary:
            return self.vocabulary.getTerm(key)
        raise KeyError(key)



def _addCollection(entity_query, data_column):
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
    value_class, value_column = _getValueColumn(data_column)
    session = entity_query.session
    is_postgres = 'postgres' in session.bind.url.drivername
    attributes = data_column.attributes
    path = data_column.path

    if data_column.selection is None:
        if not is_postgres:
            # aggregate subquery results into comma-delimited list
            value_column = sa.func.group_concat(value_column)

        column_part = (
            session.query(value_column)
            .filter(value_class.entity_id == model.Entity.id)
            .filter(value_class.attribute_id.in_([a.id for a in attributes]))
            .correlate(model.Entity)
            .as_scalar())

        if is_postgres:
            # use postgres' native array support if available
            column_part = sa.func.array(column_part)

    else:
        column_part = (
            session.query(true())
            .filter(value_class.entity_id == model.Entity.id)
            .filter(value_class.attribute_id.in_([a.id for a in attributes]))
            .filter(value_column._value == data_column.selection.value)
            .correlate(model.Entity)
            .as_scalar())

    column_part = column_part.label(data_column.name)
    entity_query = entity_query.add_column(column_part)

    return entity_query


def _addObject(entity_query, data_column, joined=None):
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
    value_class, value_column = _getValueColumn(data_column)
    attributes = data_column.attributes
    path = data_column.path

    # we're going to use this as a key in the lookup table of joined objects
    parent_name = path[0]

    if joined is not None and parent_name in joined:
        associate_class = joined[parent_name]
    else:
        # need to do an extra left join for the sub-object assocation table
        associate_class = orm.aliased(model.ValueObject, name=parent_name)
        # do a single join to the sub-object
        entity_query = entity_query.outerjoin(associate_class, (
            (model.Entity.id == associate_class.entity_id)
            & associate_class.attribute_id.in_(
                [a.schema.parent_attribute.id for a in attributes]
                )
            ))
        if joined is not None:
            # keep a reference in the lookup table
            joined[parent_name] = associate_class

    # each subsequent join should be using the lookup table
    entity_query = entity_query.outerjoin(value_class, (
        (value_class.entity_id == associate_class._value)
        & value_class.attribute_id.in_([a.id for a in attributes])
        ))

    column_part = value_column.label(data_column.name)
    entity_query = entity_query.add_column(column_part)
    return entity_query


def _addScalar(entity_query, data_column):
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
    value_class, value_column = getValueColumn(data_column)
    entity_query = entity_query.outerjoin(value_class, (
        (value_class.entity_id == datastore.Entity.id)
        & value_class.attribute_id.in_([a.id for a in attributes])
        ))
    column_part = value_column.label(data_column.name)
    entity_query = entity_query.add_column(column_part)
    return entity_query


def _getValueColumn(data_column):
    u"""
    Determines the value class and column for the attributes
    Uses the most recent type used for the attribute

    Arguments
        ``path``
            The column plan path
        ``attributes``
            The attributes in the ancestry for the given path

    Returns
        A tuple consisting of the value_class to query from as well
        as the casted column containing the actual stored value.
    """
    path = data_column.path
    attributes = data_column.attributes
    # the attribute listing should give a hint as to which session
    session = orm.object_session(attributes[-1])
    is_sqlite = session.bind.url.drivername == 'sqlite'
    # find the correct value class and alias it (for mulitple joins)
    type_name = attributes[-1].type
    source_class = storage.nameModelMap[type_name]
    value_name = u'_'.join(path + (type_name,))
    value_class = orm.aliased(source_class, name=value_name)
    # sqlite is very finicky about dates: must be function result
    if is_sqlite and type_name == u'date':
        value_column = sa.func.date(value_class._value)
    elif is_sqlite and type_name == u'datetime':
        value_column = sa.func.datetime(value_class._value)
    else:
        cast_type = storage.nameCastMap[type_name]
        value_column = sa.cast(value_class._value, cast_type)
    return value_class, value_column

