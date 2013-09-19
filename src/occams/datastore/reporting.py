u"""
A utility for allowing the access of entered schema data to be represented
in a SQL table-like fashion.
"""

from itertools import imap as map
from ordereddict import OrderedDict

import sqlalchemy as sa
from sqlalchemy import orm

from . import model


def export(schema):
    u"""
    Builds a schema entity data report query table from the data dictioanry.

    Arguments
        ``schema``
            The source schema instance

    Returns
        A SQLAlchemy aliased sub-query. Depending on the database driver,
        the result will either be an aliased subquery or a
        Common Table Expression (or CTE).

        Developer note: the results that will be returned by the subquery are
        named tuples of each result using the names of the naming schema as the
        property names.
    """
    session = orm.object_session(schema)
    is_sqlite = 'sqlite' == session.bind.url.drivername
    is_postgres = 'postgres' in session.bind.url.drivername
    query = (
        session.query(
            model.Entity.id,
            model.Entity.state_id,
            model.Entity.collect_date,
            model.Entity.is_null)
        .filter_by(schema=schema))

    for attribute in schema.itervalues():
        value_class = orm.aliased(
            model.nameModelMap[attribute.type], name=attribute.name)

        if attribute.type == 'date':
            # sqlite handles date/datetime weirdly
            value_column = (getattr(sa.func, attribute.type)(value_class._value)
                            if is_sqlite
                            else sa.cast(value_class._value, sa.Date))
        else:
            value_column = value_class._value

        filter_expression = (
            (model.Entity.id == value_class.entity_id)
            & (value_class.attribute_id == attribute.id))

        # Collections are added via correlated sub-queries to the report
        if attribute.is_collection and attribute.choices:
            for choice in attribute.choices:
                query = query.add_column(
                    session.query(
                        session
                        .query(value_class)
                        .filter(filter_expression & (value_column == choice.id))
                        .exists())
                    .correlate(model.Entity)
                    .as_scalar()
                    .label(attribute.name + '-' + str(choice.name)))
        # Scalar columns are added via LEFT OUTER JOIN
        else:
            query = query.outerjoin(value_class, filter_expression)
            if attribute.choices:
                choice_alias = orm.aliased(model.Choice, name=attribute.name + '-choice')
                query = (
                    query.outerjoin(choice_alias, value_column == choice_alias.id)
                    .add_column(choice_alias.name.label(attribute.name)))
            else:
                query = query.add_column(value_column.label(attribute.name))

    query = (
        query.add_columns(
            model.Entity.create_date,
            model.Entity.create_user_id,
            model.Entity.modify_date,
            model.Entity.modify_user_id)
        .order_by(model.Entity.id))

    return query.cte(schema.name) if not is_sqlite else query.subquery(schema.name)

