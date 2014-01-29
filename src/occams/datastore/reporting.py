"""
A utility for allowing the access of entered schema data to be represented
in a SQL table-like fashion.
"""
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from sqlalchemy import func, orm, cast, null, true, Date, Integer

from occams.datastore import model


def build_report(session, schema_name,
                 ids=None,
                 expand_collections=False,
                 use_choice_labels=False):
    """
    Builds a schema entity data report query table from the data dictioanry.

    Parameters:
    session -- The database session to use
    schema_name -- The name of the schema
    ids -- (Optional) The spcific ids to include in the report
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
    is_postgres = 'postgres' in session.bind.url.drivername

    query = (
        session.query(
            model.Entity.id.label('entity_id'),
            model.Schema.name.label('schema_name'),
            model.Schema.publish_date.label('schema_version'),
            model.State.name.label('state'),
            model.Entity.collect_date,
            cast(model.Entity.is_null, Integer).label('is_null'))
        .join(model.State)
        .join(model.Schema)
        .filter(model.Schema.name == schema_name)
        .filter(model.Schema.publish_date != null())
        .filter(model.Schema.retract_date == null()))

    if ids:
        query = query.filter(model.Schema.id.in_(ids))

    columns = build_columns(session, schema_name, ids, expand_collections)

    for column in columns.itervalues():

        # evaluate the target mapped class and casted value column
        Value = orm.aliased(model.nameModelMap[column.type])
        value_column = Value._value

        if column.type == 'date':
            # sqlite handles datetimes weirdly
            value_column = (getattr(func, column.type)(Value._value)
                            if is_sqlite else cast(Value._value, Date))

        filter_expression = (
            (model.Entity.id == Value.entity_id)
            & (Value.attribute_id.in_([a.id for a in column.attributes])))

        if column.is_collection:
            # Collections are added via correlated sub-queries to the entity
            if column.choices:
                if not is_postgres:
                    value_column = func.group.concat(value_column)

                value_column = (
                    session.query(value_column)
                    .filter(filter_expression)
                    .correlate(model.Entity)
                    .as_scalar())

                if is_postgres:
                    value_column = func.array(value_column)

            else:
                value_column = (
                    session.query(true())
                    .filter(filter_expression)
                    .filter(value_column == column.choice.name)
                    .correlate(model.Entity)
                    .as_scalar())
        else:
            # Scalar columns are added via LEFT OUTER JOIN
            query = query.outerjoin(Value, filter_expression)

            if column.choices:
                Choice = orm.aliased(model.Choice)
                query = query.outerjoin(Choice, Value._value == Choice.id)
                if use_choice_labels:
                    value_column = Choice.title
                else:
                    value_column = Choice.name

        query = query.add_column(value_column.label(column.name))

    CreateUser = orm.aliased(model.User)
    ModifyUser = orm.aliased(model.User)

    query = (
        query
        .join(CreateUser, model.Entity.create_user)
        .join(ModifyUser, model.Entity.modify_user)
        .add_columns(
            model.Entity.create_date,
            CreateUser.key.label('create_user'),
            model.Entity.modify_date,
            ModifyUser.key.label('modify_user'))
        .order_by(model.Entity.id))

    if is_sqlite:
        return query.subquery(schema_name)
    else:
        return query.cte(schema_name)


def build_columns(session, schema_name, ids=None, expand_collections=False):
    """
    Builds a ``DataDict`` for all attributes that ever existed in a schema

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
        session.query(model.Attribute)
        .join(model.Attribute.schema)
        .filter(model.Schema.name == schema_name)
        .filter(model.Schema.publish_date != null())
        .filter(model.Schema.retract_date == null()))

    if ids:
        query = query.filter(model.Schema.id.in_(ids))

    # aliased so we don't get naming ambiguity
    RecentAttribute = orm.aliased(model.Attribute)

    query = (
        query.order_by(
            (session.query(RecentAttribute.order)
                .join(RecentAttribute.schema)
                .filter(model.Schema.name == schema_name)
                .filter(model.Schema.publish_date != null())
                .filter(RecentAttribute.name == model.Attribute.name)
                .order_by(model.Schema.publish_date.desc())
                .limit(1)
                .correlate(model.Attribute)
                .as_scalar()
                .label('most_recent_attribute')).asc(),
            # oldest to newest within the lineage
            model.Schema.publish_date.asc()))

    plan = OrderedDict()
    selected = dict()
    columns = OrderedDict()

    # Organize the attributes
    for attribute in query:
        if (expand_collections
                and attribute.is_collection
                and attribute.choices):
            for choice in attribute.choices:
                name = attribute.name + '_' + choice.name
                plan.setdefault(name, []).append(attribute)
                selected[name] = choice
        else:
            plan.setdefault(attribute.name, []).append(attribute)

    # Build the final plan
    for name, attributes in plan.iteritems():
        columns[name] = DataColumn(name, attributes, selected.get(name))

    return columns


class DataColumn:
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
        self.attributes = tuple(attributes)
        self.choice = choice
        if choice is not None:
            self.choices = {}
        else:
            self.choices = dict([(c.name, c.title)
                                for a in attributes
                                for c in a.choices])

    def __getitem__(self, key):
        return self.choices[key]
