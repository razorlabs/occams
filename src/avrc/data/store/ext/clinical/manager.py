""" Defines several useful manager base classes.
"""

from zope.interface import implements

from avrc.data.store import model
from avrc.data.store.interfaces import IManager


class ConventionalManager(object):

    _model = None

    _type = None


    def __init__(self, datastore):
        self.datastore = datastore


    def putProperties(self, rslt, source):
        raise NotImplementedError("Subclasses must implement putProperties")


    def get(self, key):
        """ See `IConventionalManager.get`
        """
        session = self.datastore.session
        entry = session.query(self._model).filter_by(zid=key).first()
        result = None

        if entry is not None:
            result = self._type()
            self.putProperties(result, entry)

        return result


    def put(self, source):
        """ See `IConventionalManager.put`
        """
        session = self.datastore.session
        entry = session.query(self._model).filter_by(zid=source.zid).first()

        if entry is None:
            entry = self._model(zid=source.zid)

        # TODO: (mmartinez) This method should be able to figure it out as
        # opposed to having each class define their mapping. It all depends
        # on proper Interface setup.
        self.putProperties(entry, source)

        if not entry.id:
            session.add(entry)
        else:
            session.flush()

        session.flush()
        return source


    def retire(self, source):
        """ See `IConventionalManager.retire`
        """
        session = self.datastore.session
        rslt = session.query(self._model).filter_by(zid=source.zid).first()
        if rslt is not None:
            rslt.is_active = False
            session.flush()
        session.flush()


    def purge(self, source):
        """ See `IConventionalManager.purge`
        """
        session = self.datastore.session
        rslt = session.query(self._model).filter_by(zid=source.zid).first()
        if rslt is not None:
            session.remove(rslt)
        session.flush()


    def keys(self):
        """ See `IConventionalManager.keys`
        """
        session = self.datastore.session
        query = session.query(self._model.zid).filter_by(is_active=True)
        return [zid for zid in query.all()]


class EAVContainerManager(ConventionalManager):

    def getEnteredDataQuery(self, context, klass_name=None, state=None):

        session = self.datastore.session

        query = (
            session.query(model.Entity)
            .join(self._model.instances)
            .filter(self._model.zid == context.zid)
            .filter(model.Entity.asOf(None))
            )

        if state:
            query = query.join(model.State).filter_by(name=state)

        if klass_name:
            query = query.join(model.Schema).filter_by(name=klass_name)
            
        return query
        
    def getEnteredData(self, context):
        """ Get all of the data entered for a context
        """
        query = self.getEnteredDataQuery(self, context)
        result = [self.datastore.get(entity.name) for entity in query.all()]
        return result


    def getEnteredDataSummary(self, context, klass_name=None, state=None):

        query = self.getEnteredDataQuery(context, klass_name, state)

 
        result = []

        for entity in query.all():
            result.append(tuple([
                entity.schema.name,
                entity.schema.title,
                entity.name,
                entity.title,
                entity.state.name,
                entity.state.title
                ]))

        return tuple(result)


    def getEnteredDataCount(self, context, klass_name=None, state=None):
        query = self.getEnteredDataQuery(context, klass_name, state)
        return query.count()


    def getEnteredDataOfType(self, context, type):
        """ Get all of the data entered for a context
        """
        session = self.datastore.session

        query = (
            session.query(model.Entity)
            .join(self._model.instances)
            .filter(self._model.zid == context.zid)
            .join(model.Schema)
            .filter_by(name=type)
            )

        entity = query.first()

        if entity is not None:
            result = self.datastore.get(entity.name)
        else:
            result = None

        return result


    def addValues(self, context, values):
        """ Associates EAV values to a context.
        """
        session = self.datastore.session
        context = session.query(self._model).filter_by(zid=context.zid).first()

        if not isinstance(values, (list, tuple)):
            values = [values]

        for value in values:
            query = session.query(model.Entity).filter_by(name=value.__name__)
            entity = query.first()
            context.instances.append(entity)

        session.flush()
