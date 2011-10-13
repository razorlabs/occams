from OFS.SimpleItem import SimpleItem
from five import grok

from occams.form.interfaces import ISchemaContext


class SchemaContext(SimpleItem):
    grok.implements(ISchemaContext)

    _schema = None

    def __init__(self, schema):
        self._schema = schema
        self.Title = schema.title

    @property
    def schema(self):
        return self._schema
