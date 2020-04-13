"""
A utility for allowing the access of entered schema data to be represented
in a SQL table-like fashion.
"""
from collections import OrderedDict

import sqlalchemy as sa
from sqlalchemy import orm, cast, null, literal, Integer, case, Unicode, func
from sqlalchemy.dialects.postgresql import ARRAY

from . import models
from .utils.sql import group_concat, to_date, to_datetime


def build_report(session,
                 schema_name,
                 ids=None,
                 attributes=None,
                 expand_collections=False,
                 use_choice_labels=False,
                 context=None,
                 ignore_private=True,
                 delimiter=';'):
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
            cast(models.Entity.not_done, Integer).label('not_done'))
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

    for column in columns.values():
        if column.type == 'section':  # Sections are not used in reports
            continue

        if attributes is not None and column.name not in attributes:
            continue

        if column.is_private and ignore_private:
            query = query.add_column(literal(u'[PRIVATE]').label(column.name))
            continue

        if column.type == 'blob':
            Attachment = orm.aliased(models.EntityAttachment)
            value_column = (
                session.query(Attachment.file_name)
                    .filter(Attachment.id == models.Entity.data[column.name].astext.cast(sa.Integer))
                    .filter(Attachment.entity_id == models.Entity.id)
                    .correlate(models.Entity)
                    .as_scalar()
                )

        elif column.type == 'number':
            value_column = models.Entity.data[column.name].astext.cast(sa.Numeric)

        elif column.type == 'date':
            value_column = models.Entity.data[column.name].astext.cast(sa.Date)

        elif column.type == 'datetime':
            value_column = models.Entity.data[column.name].astext.cast(sa.DateTime)

        elif column.type in ('string', 'text'):
            value_column = models.Entity.data[column.name].astext.cast(sa.Unicode)

        # multiple choice
        elif column.type == 'choice' and column.is_collection:
            if expand_collections:
                if use_choice_labels:
                    # Query for the correspoinding label if is in the selection
                    Choice = orm.aliased(models.Choice)
                    Attribute = orm.aliased(models.Attribute)
                    value_column = (
                        session.query(Choice.title)
                            .select_from(Choice)
                            .join(Attribute)
                            .filter(Attribute.schema_id == models.Entity.schema_id)
                            .filter(Attribute.name == column.attribute_name)
                            .filter(Choice.name == column.choice.name)
                            .filter(models.Entity.data[column.attribute_name].has_key(column.choice.name))
                            .correlate(models.Entity)
                            .as_scalar()
                    )
                else:
                    # Coerce to true/false if the selection contains the choice for this column
                    value_column = models.Entity.data[column.attribute_name].has_key(column.choice.name).cast(sa.Integer)
            else:
                if use_choice_labels:
                    # Replace with corresponding selected labels for the current version of the form
                    Choice = orm.aliased(models.Choice)
                    Attribute = orm.aliased(models.Attribute)
                    value_column = (
                        session.query(func.string_agg(Choice.title, literal(delimiter)))
                            .select_from(Choice)
                            .join(Attribute)
                            .filter(Attribute.schema_id == models.Entity.schema_id)
                            .filter(Attribute.name == column.attribute_name)
                            .filter(models.Entity.data[column.name].has_key(Choice.name))
                            .correlate(models.Entity)
                            .as_scalar()
                    )
                else:
                    # expand the json array a a listing of values
                    selected_subquery = (
                        session.query(
                            func.jsonb_array_elements_text(models.Entity.data[column.name]).label('selected')
                        )
                        .subquery()
                    )
                    # aggregate the elisting of values as a single delimited list
                    value_column = (
                        session.query(func.string_agg(selected_subquery.c.selected, literal(delimiter)))
                        .as_scalar()
                    )

        # single choice
        elif column.type == 'choice' and not column.is_collection:
            # default behavior is to use the code directly as a value
            value_column = models.Entity.data[column.name].astext.cast(sa.Unicode)

            if use_choice_labels:
                # use a subquery to replace the code with the choice label
                Choice = orm.aliased(models.Choice)
                Attribute = orm.aliased(models.Attribute)
                value_column = (
                    session.query(Choice.title)
                        .select_from(Choice)
                        .join(Attribute)
                        .filter(Attribute.schema_id == models.Entity.schema_id)
                        .filter(Attribute.name == column.name)
                        .filter(Choice.name == value_column)
                        .correlate(models.Entity)
                        .as_scalar()
                )

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

    if is_sqlite:
        cte = query.subquery(schema_name)
    else:
        cte = query.cte(schema_name)

    print(cte)
    return cte


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
        .filter(models.Schema.retract_date == null())
        .filter(models.Attribute.type != u'section'))

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
                and attribute.type == 'choice'):
            for choice in attribute.choices.values():
                name = attribute.name + '_' + choice.name
                plan.setdefault(name, []).append(attribute)
                selected[name] = choice
        else:
            plan.setdefault(attribute.name, []).append(attribute)

    # Build the final plan
    for name, attributes in plan.items():
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
        self.attribute_name = attributes[-1].name
        self.type = types.pop()
        self.is_collection = collections.pop()
        self.is_private = any(a.is_private for a in attributes)
        self.attributes = tuple(attributes)
        self.choice = choice
        if choice is not None:
            self.choices = {}
        else:
            self.choices = dict((c.name, c.title)
                                for a in attributes
                                for c in a.choices.values())
