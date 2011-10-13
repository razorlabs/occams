
from five import grok

from occams.form.interfaces import ISchemaContext


class SchemaContext(grok.Model):
    grok.implements(ISchemaContext)

    _schema = None

    def __init__(self, schema):
        super(SchemaContext, self).__init__(schema.name)
        self._schema = schema
        self.title = schema.title
        self.Title = schema.title

    @property
    def schema(self):
        return self._schema
