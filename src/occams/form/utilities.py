from five import grok
from avrc.data.store import DataStore
from avrc.data.store.interfaces import IDataStore
from occams.form.interfaces import IRepository

@grok.adapter(IRepository)
@grok.implementer(IDataStore)
def getDataStore(context):
    fmt = '%(vendor)s://%(user)s:%(password)s@%(host)s/%(database)s'
    url = fmt % context.__dict__
    return DataStore.create(url)



