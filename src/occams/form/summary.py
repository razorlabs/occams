"""
Form summary tools
"""

from zope.interface import implements

from sqlalchemy import func
from sqlalchemy import String
from sqlalchemy import Date
from sqlalchemy.sql.expression import case
from sqlalchemy.sql.expression import cast
from sqlalchemy.sql.expression import null
from sqlalchemy.sql.expression import literal_column
from sqlalchemy.orm import aliased

from occam.datastore import model
from occams.form.interfaces import IFormSummary
from occams.form.interfaces import IFormSummaryGenerator


def literal(value):
    """
    Helper method to convert a Python value into a SQL string
    """
    return literal_column('\'%s\'' % str(value), String)


def changeTableFactory(session):
    """
    Helper method to generate a SQLAlchemy expression table for schemata changes.
    The result set will include all modifications done to each schema.
    """
    SubSchema = aliased(model.Schema, name='_subschema')
    SubAttribute = aliased(model.Attribute, name='_subattribute')

    # A query that builds a revision log result set of all master forms,
    # which also include the revisions of subforms
    query = (
        # Master schema create dates
        session.query(
            model.Schema.name.label('schema_name'),
            null().label('attribute_name'),
            model.Schema.create_date.label('change_date'),
            )
        .union(
            # Master schema removal dates
            session.query(model.Schema.name, null(), model.Schema.remove_date),

            # Master schema attribute create dates
            session.query(
                model.Schema.name,
                # Only report non-object values as part of the field count
                case([
                    (model.Attribute.type != literal('object'),
                        (model.Schema.name + literal('.') + model.Attribute.name))
                    ]),
                model.Attribute.create_date
                )
            .join((model.Attribute, (model.Attribute.schema_id == model.Schema.id))),

            # Master schema attribute removal dates
            session.query(model.Schema.name, null(), model.Attribute.remove_date)
            .join((model.Attribute, (model.Attribute.schema_id == model.Schema.id))),

            # Sub schema create dates
            session.query(model.Schema.name, null(), SubSchema.create_date)
            .join((model.Attribute, (model.Attribute.schema_id == model.Schema.id)))
            .join((SubSchema, (SubSchema.id == model.Attribute.object_schema_id))),

            # Sub schema removal dates
            session.query(model.Schema.name, null(), SubSchema.remove_date)
            .join((model.Attribute, (model.Attribute.schema_id == model.Schema.id)))
            .join((SubSchema, (SubSchema.id == model.Attribute.object_schema_id))),

            # Sub schema attribute create dates
            session.query(
                model.Schema.name,
                SubSchema.name + literal('.') + SubAttribute.name,
                SubAttribute.create_date,
                )
            .join((model.Attribute, (model.Attribute.schema_id == model.Schema.id)))
            .join((SubSchema, (SubSchema.id == model.Attribute.object_schema_id)))
            .join((SubAttribute, (SubAttribute.schema_id == SubSchema.id))),

            # Sub schema attribute removal dates
            session.query(model.Schema.name, null(), SubAttribute.remove_date,)
            .join((model.Attribute, (model.Attribute.schema_id == model.Schema.id)))
            .join((SubSchema, (SubSchema.id == model.Attribute.object_schema_id)))
            .join((SubAttribute, (SubAttribute.schema_id == SubSchema.id))),
            )
        )

    return query.subquery('_change')


def baseSchemaNamesTableFactory(session):
    """
    Helper method to generate a SQLAlchemy expression table for base schemata names
    """
    BaseSchema = aliased(model.Schema, name='_base')

    # A query that builds a base schema name result set
    query = (
        session.query(BaseSchema.name)
        .join((model.Schema, (model.Schema.base_schema_id == BaseSchema.id)))
        .group_by(BaseSchema.name)
        )

    return query.subquery()


def subSchemaNamesTableFactory(session):
    """
    Helper method to generate a SQLAlchemy expression table for sub schemata names
    """
    query = (
        session.query(model.Schema.name)
        .join((model.Attribute, (model.Attribute.object_schema_id == model.Schema.id)))
        .group_by(model.Schema.name)
        )

    return query.subquery()


def summaryTableFactory(session):
    """
    Helper method to generate a SQLAlchemy expression table for form summaries
    """
    changeTable = changeTableFactory(session)

    # Summary report table for each schema
    query = (
        session.query(
            changeTable.c.schema_name.label('name'),
            func.count(changeTable.c.attribute_name.distinct()).label('fieldCount'),
            func.count(cast(changeTable.c.change_date, Date).distinct()).label('revisionCount'),
            (func.count() - literal('1')).label('changeCount'),
            func.max(changeTable.c.change_date).label('currentVersion'),
            func.min(changeTable.c.change_date).label('createdOn'),
            )
        .select_from(changeTable)
        .group_by(changeTable.c.schema_name)
        )
    return query.subquery('_summary')


class DataStoreSchemaSummary(object):
    implements(IFormSummary)

    _values = None

    def __init__(self, *args, **kwargs):
        self._values = dict()
        # Get items according to the interface specification
        for name, item in kwargs.items():
            if name in IFormSummary:
                self._values[name] = item
            else:
                raise AttributeError

        self._values['name'] = str(self._values['name'])

    @classmethod
    def fromSql(cls, raw):
        """
        Helper method to construct from a SQL result
        """
        attributes = dict([(name, getattr(raw, name)) for name in IFormSummary.names()])
        return cls(**attributes)

    def __getattr__(self, name):
        if name not in self._values:
            raise AttributeError
        return self._values.get(name)


class FormSummaryGenerator(object):
    implements(IFormSummaryGenerator)

    def getItems(self, session):
        summaryTable = summaryTableFactory(session)
        baseSchemaNamesTable = baseSchemaNamesTableFactory(session)
        subSchemaNamesTable = subSchemaNamesTableFactory(session)

        # Final result set, only report master schemata and leaf schemata
        query = (
            session.query(
                model.Schema.name.label('name'),
                model.Schema.title.label('title'),
                summaryTable.c.fieldCount,
                summaryTable.c.changeCount,
                summaryTable.c.revisionCount,
                summaryTable.c.currentVersion,
                summaryTable.c.createdOn,
                )
            .select_from(model.Schema)
            .join((summaryTable, (model.Schema.name == summaryTable.c.name)))
            .filter(~model.Schema.name.in_(baseSchemaNamesTable))
            .filter(~model.Schema.name.in_(subSchemaNamesTable))
            .filter(model.Schema.asOf(None))
            .order_by(model.Schema.title)
            )

        # Wrap the results into objects Zope can understand
        items = [DataStoreSchemaSummary.fromSql(r) for r in query.all()]

        return items
