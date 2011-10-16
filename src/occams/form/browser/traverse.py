from five import grok
from grokcore.traverser import Traverser

from avrc.data.store import model
from avrc.data.store.interfaces import IDataStore

from occams.form import MessageFactory as _
from occams.form import Logger as log
from occams.form.context import SchemaContext
from occams.form.interfaces import IRepository


class RepositoryTraverse(Traverser):
    grok.context(IRepository)

    def traverse(self, name):
        datastore = IDataStore(self.context)
        session = datastore.session

        log.debug(u'Traversing to form "%s"' % name)

        query = (
            session.query(model.Schema)
            .filter(model.Schema.name == name)
            .filter(model.Schema.asOf(None))
            .order_by(model.Schema.name.asc())
            )

        schema = query.first()

        if schema is not None:
            return SchemaContext(schema).__of__(self.context)
