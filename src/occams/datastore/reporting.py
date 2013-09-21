u"""
A utility for allowing the access of entered schema data to be represented
in a SQL table-like fashion.
"""

from itertools import imap as map
from ordereddict import OrderedDict

import sqlalchemy as sa
from sqlalchemy import and_, orm

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
    query = (
        session.query(
            model.Entity.id,
            model.Entity.state_id,
            model.Entity.collect_date,
            sa.cast(model.Entity.is_null, sa.Integer).label('is_null'))
        .filter_by(schema=schema))

    for attribute in schema.itervalues():
        value_alias = orm.aliased(model.nameModelMap[attribute.type])
        if attribute.is_collection and attribute.choices:
            for choice in attribute.choices:
                query = query.add_column(
                    sa.cast(
                        session.query(value_alias)
                        .filter(value_alias.entity_id == model.Entity.id)
                        .filter(value_alias._value == choice.id)
                        .correlate(model.Entity)
                        .exists(),
                        sa.Integer)
                    .label(attribute.name + '-' + str(choice.name)))
        else:
            query = (
                query
                .outerjoin(value_alias, and_(
                    (value_alias.entity_id == model.Entity.id),
                    (value_alias.attribute_id == attribute.id))))
            if attribute.choices:
                choice_alias = orm.aliased(model.Choice)
                query = (
                    query.outerjoin(choice_alias, value_alias._value == choice_alias.id)
                    .add_column(choice_alias.name.label(attribute.name)))
            else:
                query = query.add_column(value_alias._value.label(attribute.name))

    query = (
        query.add_columns(
            model.Entity.create_date,
            model.Entity.create_user_id,
            model.Entity.modify_date,
            model.Entity.modify_user_id)
        .order_by(model.Entity.id))

    return query.cte(schema.name)

