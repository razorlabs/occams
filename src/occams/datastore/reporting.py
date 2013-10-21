u"""
A utility for allowing the access of entered schema data to be represented
in a SQL table-like fashion.
"""

from itertools import imap as map
from ordereddict import OrderedDict

import sqlalchemy as sa
from sqlalchemy import and_, func, orm

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

    aggregate = lambda c: (
        sa.func.array_to_string(sa.func.array_agg(c), sa.literal(','))
            if is_postgres
            else sa.func.group_concat(c))

    CreateUser = orm.aliased(model.User)
    ModifyUser = orm.aliased(model.User)

    query = (
        session.query(
            model.Entity.id.label('entity_id'),
            model.Entity.state_id.label('state'),
            model.Entity.collect_date,
            sa.cast(model.Entity.is_null, sa.Integer).label('is_null'))
        .filter_by(schema=schema))

    for attribute in schema.itervalues():
        Value = orm.aliased(model.nameModelMap[attribute.type])
        if attribute.is_collection and attribute.choices:
            Choice = orm.aliased(model.Choice)
            query = query.add_column(
                session.query(aggregate(Choice.name))
                .select_from(Value)
                .filter(Value.entity_id == model.Entity.id)
                .filter(Value.attribute_id == attribute.id)
                .join(Choice, Value.value)
                .correlate(model.Entity)
                .as_scalar()
                .label(attribute.name))
        else:
            query = (
                query
                .outerjoin(Value, and_(
                    (Value.entity_id == model.Entity.id),
                    (Value.attribute_id == attribute.id))))
            if attribute.choices:
                Choice = orm.aliased(model.Choice)
                query = (
                    query.outerjoin(Choice, Value._value == Choice.id)
                    .add_column(Choice.name.label(attribute.name)))
            else:
                query = query.add_column(Value._value.label(attribute.name))

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

    return query.cte(schema.name)

