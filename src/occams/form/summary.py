"""
Form summary tools
"""

from zope.interface import implements
from AccessControl import getSecurityManager

from sqlalchemy import func
from sqlalchemy import String
from sqlalchemy.sql.expression import literal_column
from sqlalchemy.orm import aliased

from occams.datastore import model
from occams.form.interfaces import IFormSummary
from occams.form.interfaces import IFormSummaryGenerator


def literal(value):
    """
    Helper method to convert a Python value into a SQL string
    """
    return literal_column('\'%s\'' % str(value), String)

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
        DAVE : THIS MAKES DICT FROM QUERY ITEMS
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
        current_user = getSecurityManager().getUser().getId()
        SubSchema = aliased(model.Schema, name='_subschema')
        SubAttribute = aliased(model.Attribute, name='_subattribute')
        FieldCount = (
            session.query(model.Schema.id.label('schema_id'),
                                 func.count(model.Schema.id).label('field_count'))
                .select_from(model.Schema)
                .outerjoin(model.Attribute, model.Schema.id == model.Attribute.schema_id)
                .outerjoin(SubSchema, SubSchema.id == model.Attribute.object_schema_id)
                .outerjoin(SubAttribute, SubSchema.id == SubAttribute.schema_id)
                .filter(~model.Schema.is_inline) 
                .group_by(model.Schema.id)
                ).subquery('fieldcount')

        # EditVersion = (
        #     session.query(
        #         model.Schema.id.label('schema_id'),
        #         SubSchema.id.label('draft_id'),
        #         )
        #         .select_from(model.Schema)
        #         .join(SubSchema, model.Schema.name == SubSchema.name)
        #         .join(model.User, SubSchema.create_user_id == model.User.id)
        #         .filter(SubSchema.state == 'draft')
        #         .filter(model.User.key == current_user)
        #         .order_by(SubSchema.create_date.desc())
        #     ).subquery('editversion')

        MaxDate = (
            session.query(
                model.Schema.name.label('name'),
                func.max(model.Schema.publish_date).label('publish_date')
                )
                .filter(model.Schema.is_inline == False)
                .filter(model.Schema.state == 'published')
                .filter(model.Schema.publish_date != None)
                .group_by(model.Schema.name)
            ).subquery('maxversion')

        query = (
            session.query(model.Schema.id.label('id'),
                                 model.Schema.name.label('name'),
                                 model.Schema.title.label('title'),
                                 FieldCount.c.field_count.label('field_count'),
                                 model.Schema.revision.label('revision'),
                                 model.Schema.state.label('state'),
                                 model.User.key.label('create_user'),
                                 model.Schema.create_date.label('create_date'),
                                 model.Schema.publish_date.label('publish_date'),
                                 (model.Schema.publish_date == MaxDate.c.publish_date).label('is_current'),
                                 # EditVersion.c.draft_id.label('draft_id'),
                                 ((model.Schema.state.in_(['draft', 'review'])) & (model.User.key == current_user)).label('is_editable')
                                 )
            .join(FieldCount, model.Schema.id == FieldCount.c.schema_id)
            .join(model.User, model.Schema.create_user_id == model.User.id)
            .outerjoin(MaxDate, model.Schema.name == MaxDate.c.name)
            # .outerjoin(EditVersion, model.Schema.id == EditVersion.c.schema_id)
            .filter(model.Schema.is_inline == False)
            .filter(model.Schema.state != 'retracted')
            .order_by(model.Schema.title.asc(), model.Schema.publish_date.desc().nullslast())
            )

        items = [DataStoreSchemaSummary.fromSql(r) for r in query.all()]
        return items
