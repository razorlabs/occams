"""
Form summary tools
"""

from sqlalchemy import func
from sqlalchemy.sql.expression import case
from sqlalchemy.sql.expression import null
from sqlalchemy.orm import aliased

from five import grok

from avrc.data.store import model

from occams.form.interfaces import IFormSummary
from occams.form.interfaces import IFormSummaryGenerator


class DataStoreSchemaSummary(object):
    grok.implements(IFormSummary)

    _values = None

    def __init__(self, *args, **kwargs):
        self._values = dict()
        for name, item in kwargs.items():
            if name in IFormSummary:
                self._values[name] = item
            else:
                raise AttributeError

        self._values['name'] = str(self._values['name'])

    @classmethod
    def fromResult(cls, raw):
        attributes = dict([(name, getattr(raw, name)) for name in IFormSummary.names()])
        return cls(**attributes)

    def __getattr__(self, name):
        if name not in self._values:
            raise AttributeError
        return self._values.get(name)


class FormSummaryGenerator(grok.GlobalUtility):
    grok.implements(IFormSummaryGenerator)

    def getItems(self, session):
        BaseSchema = aliased(model.Schema, name='base')

        # A query that builds a base schema name result set
        baseSchemaNamesQuery = (
            session.query(BaseSchema.name)
            .join((model.Schema, (model.Schema.base_schema_id == BaseSchema.id)))
            .group_by(BaseSchema.name)
            )

        # A query that builds a sub-object schema name result set
        subSchemaNamesQuery = (
            session.query(model.Schema.name)
            .join((model.Entity, (model.Entity.schema_id == model.Schema.id)))
            .join((model.ValueObject, (model.ValueObject.value == model.Entity.id)))
            .group_by(model.Schema.name)
            )

        SubSchema = aliased(model.Schema, name='subschema')
        SubAttribute = aliased(model.Attribute, name='subattribute')

        # A query that builds a revision log result set of all master forms,
        # which also include the revisions of subforms
        logQuery = (
            session.query(
                model.Schema.name.label('schema_name'),
                null().label('attribute_name'),
                model.Schema.create_date.label('revision_date'),
                )
            .union(

                session.query(model.Schema.name, null(), model.Schema.remove_date)
                ,

                session.query(
                    model.Schema.name,
                    case([
                        (model.Attribute.type == 'object',
                            (model.Schema.name + '.' + model.Attribute.name))
                        ]),
                    model.Attribute.create_date
                    )
                .join((model.Attribute, (model.Attribute.schema_id == model.Schema.id)))
                ,

                session.query(model.Schema.name, null(), model.Attribute.remove_date)
                .join((model.Attribute, (model.Attribute.schema_id == model.Schema.id)))
                ,

                session.query(model.Schema.name, null(), SubSchema.create_date)
                .join((model.Attribute, (model.Attribute.schema_id == model.Schema.id)))
                .join((SubSchema, (SubSchema.id == model.Attribute.object_schema_id)))
                ,

                session.query(model.Schema.name, null(), SubSchema.remove_date)
                .join((model.Attribute, (model.Attribute.schema_id == model.Schema.id)))
                .join((SubSchema, (SubSchema.id == model.Attribute.object_schema_id)))
                ,

                session.query(
                    model.Schema.name,
                    SubSchema.name + '.' + SubAttribute.name,
                    SubAttribute.create_date,
                    )
                .join((model.Attribute, (model.Attribute.schema_id == model.Schema.id)))
                .join((SubSchema, (SubSchema.id == model.Attribute.object_schema_id)))
                .join((SubAttribute, (SubAttribute.schema_id == SubSchema.id)))
                ,

                session.query(model.Schema.name, null(), SubAttribute.create_date,)
                .join((model.Attribute, (model.Attribute.schema_id == model.Schema.id)))
                .join((SubSchema, (SubSchema.id == model.Attribute.object_schema_id)))
                .join((SubAttribute, (SubAttribute.schema_id == SubSchema.id)))
                ,
                )
            )

        logSubQuery = logQuery.subquery('summary_log')

        # Now that we have the log sub query, we can build the result set
        summaryQuery = (
            session.query(
                model.Schema.name,
                model.Schema.title,
                func.count(logSubQuery.c.attribute_name.distinct()).label('fieldCount'),
                (func.count() - '1').label('revisionCount'),
                func.min(logSubQuery.c.revision_date).label('currentVersion'),
                func.max(logSubQuery.c.revision_date).label('createdOn'),
                )
            .select_from(model.Schema)
            .join((logSubQuery, (model.Schema.name == logSubQuery.c.schema_name)))
            .filter(~logSubQuery.c.schema_name.in_(baseSchemaNamesQuery.subquery()))
            .filter(~logSubQuery.c.schema_name.in_(subSchemaNamesQuery.subquery()))
            .filter(model.Schema.remove_date == None)
            .group_by(model.Schema.name, model.Schema.title)
            .order_by(model.Schema.name)
            )

        items = [DataStoreSchemaSummary.fromResult(r) for r in summaryQuery.all()]

        return items
