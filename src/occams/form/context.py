
from five import grok

from occams.form.interfaces import IDataBaseItemContext
from occams.form.interfaces import ISchemaContext


class DataBaseItemContext(grok.Model):
    grok.implements(IDataBaseItemContext)

    _item = None

    def __init__(self, item):
        super(DataBaseItemContext, self).__init__(item.name)
        self._item = item
        self.title = item.title

    @property
    def item(self):
        return self._item


class SchemaContext(DataBaseItemContext):
    grok.implements(ISchemaContext)
