"""
A utility for allowing the access of entered schema data to be represented
in a SQL table-like fashion.
"""
try:
    from collections import OrderedDict
except ImportError:  # pragma: nocover
    from ordereddict import OrderedDict

from six import itervalues, iteritems
from sqlalchemy import orm, cast, null, literal, Integer, case, Unicode

from . import models
from .utils.sql import group_concat, to_date, to_datetime


def build_report(session,
                 schema_name,
                 ids=None,
                 attributes=None,
                 expand_collections=False,
                 use_choice_labels=False,
                 context=None,
                 ignore_private=True):
    """
    Builds a schema entity data report query table from the data dictioanry.

    Parameters:
    session -- The database session to use
    schema_name -- The name of the schema
    ids -- (Optional) The spcific ids to include in the report
    attributes -- (Optional) Only include the specified attribute names
                  (default: if None, all attributes will be used)
    expand_collections -- (Optional) Expands collections to their own column
                         (default is False)
    use_choice_labels -- (Optional) Uses choice labels instead of codes
                         (default is False)

    Returns:
    A SQLAlchemy aliased sub-query. Depending on the database driver,
    the result will either be an aliased subquery or a
    Common Table Expression (or CTE).

    Developer note: the results that will be returned by the subquery are
    named tuples of each result using the names of the naming schema as the
    property names.
    """
    is_sqlite = 'sqlite' == session.bind.url.drivername

    query = (
        session.query(
            models.Entity.id.label('id'),
            models.Schema.name.label('form_name'),
            models.Schema.publish_date.label('form_publish_date'),
            models.State.name.label('state'),
            models.Entity.collect_date.label('collect_date'),
            cast(models.Entity.is_null, Integer).label('is_null'))
        .outerjoin(models.State)
        .join(models.Schema)
        .filter(models.Schema.name == schema_name)
        .filter(models.Schema.publish_date != null())
        .filter(models.Schema.retract_date == null()))

    if ids:
        query = query.filter(models.Schema.id.in_(ids))

    if context:
        query = (
            query
            .join(models.Context, (
                (models.Context.external == context)
                & (models.Context.entity_id == models.Entity.id)))
            .add_column(models.Context.key.label('context_key')))

    columns = build_columns(session, schema_name, ids, expand_collections)

    attributes = None if attributes is None else set(attributes)

    for column in itervalues(columns):
        if attributes is not None and column.name not in attributes:
            continue

        if column.is_private and ignore_private:
            query = query.add_column(literal(u'[PRIVATE]').label(column.name))
            continue

        # evaluate the target mapped class and casted value column
        Value = orm.aliased(models.nameModelMap[column.type])
        value_column = Value._value

        if column.type in ('date', 'datetime'):
            # Cast datetimes to match their attribute types
            conv = to_date if column.type == 'date' else to_datetime
            value_column = conv(Value._value)

        if column.type == 'blob':
            value_column = case(
                whens=[((value_column != null()), literal(u'[FILE]'))],
                else_=null())

        filter_expression = (
            (models.Entity.id == Value.entity_id)
            & (Value.attribute_id.in_([a.id for a in column.attributes])))

        Choice = orm.aliased(models.Choice)

        if column.is_collection:
            # Collections are added via correlated sub-queries to the entity
            if not expand_collections:

                if use_choice_labels:
                    value_column = Choice.title
                else:
                    value_column = Choice.name

                # Not all vendors suppoar ARRAY, so we just concatenate the
                # and let clients deal with spliting
                value_column = (
                    session.query(group_concat(value_column, ';'))
                    .select_from(Value)
                    .filter(filter_expression)
                    .join(Choice)
                    .group_by(Value.attribute_id)
                    .correlate(models.Entity)
                    .as_scalar())

            else:
                selected_exists = (
                    session.query(Value)
                    .join(Choice, Value._value == Choice.id)
                    .filter(filter_expression)
                    .filter(Choice.name == column.choice.name)
                    .correlate(models.Entity)
                    .exists())

                if use_choice_labels:
                    selected_value_column = (
                        session.query(
                            cast(literal(column.choice.title), Unicode))
                        .filter(selected_exists)
                        .as_scalar())
                else:
                    selected_value_column = (
                        session.query(cast(selected_exists, Integer))
                        .as_scalar())

                is_selected = (
                    session.query(Value)
                    .filter(filter_expression)
                    .correlate(models.Entity)
                    .exists())

                value_column = case([(is_selected, selected_value_column)])

        else:
            # Scalar columns are added via LEFT OUTER JOIN
            query = query.outerjoin(Value, filter_expression)

            if column.type == 'choice':
                Choice = orm.aliased(models.Choice)
                query = query.outerjoin(Choice, Value._value == Choice.id)
                if use_choice_labels:
                    value_column = Choice.title
                else:
                    value_column = Choice.name

        query = query.add_column(value_column.label(column.name))

    CreateUser = orm.aliased(models.User)
    ModifyUser = orm.aliased(models.User)

    query = (
        query
        .join(CreateUser, models.Entity.create_user)
        .join(ModifyUser, models.Entity.modify_user)
        .add_columns(
            models.Entity.create_date,
            CreateUser.key.label('create_user'),
            models.Entity.modify_date,
            ModifyUser.key.label('modify_user'))
        .order_by(models.Entity.id))

    return query.cte(schema_name) \
        if not is_sqlite else query.subquery(schema_name)


def build_columns(session, schema_name, ids=None, expand_collections=False):
    """
    Helper method to determine the columns of the report to generate

    The columns reported are only the basic data types.

    Note that the final columns are ordered by most recent order number within
    the parent, then by the parent's publication date (oldest to newest).

    Attribute lineages are are ordered by their most recent position in the
    schema, then by oldest to newest within the lineage.

    Paramters:
    session -- The session to query plan from
    schema_name -- The name of the schema to get columns plans for
    ids -- (Optional) Specific id numbers of the forms
    expand_collections -- (Optional) Also expands multiple choice attributes
                         into individual "flag" boolean columns.

    Returns:
    An ordered dictionary using the path to the attribute as the key,
    and the associated attribute list as the value. The path will
    also contain the attribute's checksum.
    """

    query = (
        session.query(models.Attribute)
        .join(models.Attribute.schema)
        .filter(models.Schema.name == schema_name)
        .filter(models.Schema.publish_date != null())
        .filter(models.Schema.retract_date == null()))

    if ids:
        query = query.filter(models.Schema.id.in_(ids))

    # aliased so we don't get naming ambiguity
    RecentAttribute = orm.aliased(models.Attribute)

    query = (
        query.order_by(
            (session.query(RecentAttribute.order)
                .join(RecentAttribute.schema)
                .filter(models.Schema.name == schema_name)
                .filter(models.Schema.publish_date != null())
                .filter(RecentAttribute.name == models.Attribute.name)
                .order_by(models.Schema.publish_date.desc())
                .limit(1)
                .correlate(models.Attribute)
                .as_scalar()
                .label('most_recent_attribute')).asc(),
            # oldest to newest within the lineage
            models.Schema.publish_date.asc()))

    plan = OrderedDict()
    selected = dict()
    columns = OrderedDict()

    # Organize the attributes
    for attribute in query:
        if (expand_collections
                and attribute.is_collection
                and attribute.choices):
            for choice in itervalues(attribute.choices):
                name = attribute.name + '_' + choice.name
                plan.setdefault(name, []).append(attribute)
                selected[name] = choice
        else:
            plan.setdefault(attribute.name, []).append(attribute)

    # Build the final plan
    for name, attributes in iteritems(plan):
        columns[name] = DataColumn(name, attributes, selected.get(name))

    return columns


class DataColumn(object):
    """
    A data dictionary column for reference when inspecting a report column.

    Note that this type is intended to be read-only.

    This type also behaves as a dictionary, granting access to vocabulary
    terms (if the underlying attributes have specified choices).
    """

    def __init__(self, name, attributes, choice=None):
        """
        Parameters:
        name -- the column name (usually the attribute name)
        attributes -- the attributes that make up this column
        choice -- (optional) if expanding choices, the one represented
                  by this column
        """
        types = set([a.type for a in attributes])
        collections = set([a.is_collection for a in attributes])
        assert len(types) == 1, '%s has amibigious type: %s' % (name, types)
        assert len(collections) == 1, '%s has amibiguous length' % name
        self.name = name
        self.type = types.pop()
        self.is_collection = collections.pop()
        self.is_private = any(a.is_private for a in attributes)
        self.attributes = tuple(attributes)
        self.choice = choice
        if choice is not None:
            self.choices = {}
        else:
            self.choices = dict([(c.name, c.title)
                                for a in attributes
                                for c in itervalues(a.choices)])
