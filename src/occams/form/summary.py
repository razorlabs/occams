"""
Form summary tools
"""

from sqlalchemy.orm import object_session
from sqlalchemy import func

from five import grok

from avrc.data.store import model
from avrc.data.store.interfaces import ISchema

from occams.form.interfaces import IFormSummary

class DataStoreSchemaSummary(grok.Adapter):
    grok.implements(IFormSummary)
    grok.context(ISchema)

    #TODO: need to use datastore's methods for completeness

    _fieldCount = None
    _revisionCount = None
    _createdOn = None
    _currentVersion = None

    def __init__(self, context):
        super(DataStoreSchemaSummary, self).__init__(context)

    @property
    def title(self):
        return self.context.title

    @property
    def fieldCount(self):
        if self._fieldCount is None:
            count = 0
            session = object_session(self.context)
            query = (
                session.query(model.Attribute)
                .filter(model.Attribute.schema.has(name=self.context.name))
                .filter(model.Attribute.asOf(None))
                )

            # Count the number of fields in sub forms, but don't include
            # the object reference field itself
            for attribute in query.filter_by(type='object').all():
                count += IFormSummary(attribute.object_schema).fieldCount

            # Sum the rest of the attributes
            count += query.filter(model.Attribute.type != 'object').count()

            self._fieldCount = count
        return self._fieldCount

    @property
    def revisionCount(self):
        if self._revisionCount is None:
            session = object_session(self.context)
            query = (
                session.query(model.Schema.create_date.label('even_date'))
                .filter(model.Schema.name == self.context.name)
                .union(
                    session.query(model.Schema.remove_date)
                    .filter(model.Schema.name == self.context.name)
                    .filter(model.Schema.remove_date != None)
                    ,
                    session.query(model.Attribute.create_date)
                    .filter(model.Attribute.schema.has(name=self.context.name))
                    ,
                    session.query(model.Attribute.remove_date)
                    .filter(model.Attribute.schema.has(name=self.context.name))
                    .filter(model.Attribute.remove_date != None)
                    )
                )
            import pdb; pdb.set_trace()
            self._revisionCount = query.count()
        return self._revisionCount

    @property
    def createdOn(self):
        if self._createdOn is None:
            session = object_session(self.context)
            query = (
                session.query(func.min(model.Schema.create_date))
                .filter(model.Schema.name == self.context.name)
                )
            (self._createdOn,) = query.first()
        return self._createdOn

    @property
    def currentVersion(self):
        if self._currentVersion is None:
            session = object_session(self.context)
            query = (
                session.query(model.Schema.create_date.label('event_date'))
                .filter(model.Schema.name == self.context.name)
                .union(
                    session.query(model.Schema.remove_date)
                    .filter(model.Schema.name == self.context.name)
                    .filter(model.Schema.remove_date != None)
                    ,
                    session.query(model.Attribute.create_date)
                    .filter(model.Attribute.schema.has(name=self.context.name))
                    ,
                    session.query(model.Attribute.remove_date)
                    .filter(model.Attribute.schema.has(name=self.context.name))
                    .filter(model.Attribute.remove_date != None)
                    )
                .order_by('event_date DESC')
                )
            (self._currentVersion,) = query.first()
        return self._currentVersion

