""" Defines several useful manager base classes.
"""

import transaction
from zope.component import createObject

from avrc.data.store import model

class AbstractDatastoreManager(object):

    def __init__(self, datastore):
        self._datastore = datastore

    def keys():
        raise NotImplementedError

    def has(key):
        raise NotImplementedError

    def get(key):
        raise NotImplementedError

    def purge(key):
        raise NotImplementedError

    def retire(key):
        raise NotImplementedError

    def restore(key):
        raise NotImplementedError

    def put(target):
        raise NotImplementedError


class AbstractDatastoreConventionalManager(AbstractDatastoreManager):
    """ See `IConventionalManager`
    """

    _model = None

    _type = None


    def queryModel(self, session, source=None, key=None):
        raise NotImplementedError("Subclasses must implement queryModel")


    def putProperties(self, rslt, source):
        raise NotImplementedError("Subclasses must implement putProperties")


    def get(self, key):
        """ See `IConventionalManager.get`
        """
        Session = self._datastore.getScopedSession()
        rslt = Session.query(self._model).filter_by(zid=key).first()
        newObj = self._type()
        newObj = self.putProperties(newObj, rslt)
        return newObj


    def put(self, source):
        """ See `IConventionalManager.put`
        """
        Session = self._datastore.getScopedSession()
        rslt = Session.query(self._model).filter_by(zid=source.zid).first()

        if rslt is None:
            rslt = self._model(zid=source.zid)
            Session.add(rslt)

        # won't update the code
        rslt = self.putProperties(rslt, source)
        transaction.commit()
        return source


    def purge(self, source):
        """ See `IConventionalManager.purge`
        """
        Session = self._datastore.getScopedSession()
        rslt = Session.query(self._model).filter_by(zid=source.zid).first()
        if rslt is not None:
            Session.remove(rslt)
        transaction.commit()


    def keys(self):
        """ See `IConventionalManager.keys`
        """
        listing = []
        Session = self._datastore.getScopedSession()
        for rslt in Session.query(self._model).all():
            newObj = createObject(self._type)
            newObj = self.putProperties(newObj, rslt)
            listing.append(newObj)

        return listing


class AbstractEAVContainerManager(AbstractDatastoreManager):
    """
    """

    def getEnteredData(self, context):
        """ Get all of the data entered for a context
        """
        Session = self._datastore.getScopedSession()
        objects = []

        instance_query = Session.query(model.Instance)\
            .join(self._model.instances)\
            .filter(self._model.zid==context.zid)

        for instance in instance_query.all():
            objects.append(self._datastore.get(instance.title))

        return objects


    def getEnteredDataSummary(self, context, klass_name=None, state=None):
        """
        """
        Session = self._datastore.getScopedSession()
        names = []

        schema_query = Session.query(model.Instance)\
            .join(self._model.instances)\
            .filter(self._model.zid == context.zid)\

        if state:
            schema_query = schema_query \
                .join(model.State)\
                .filter_by(name=state)

        if klass_name:
            schema_query = schema_query \
                .join(model.Schema)\
                .join(model.Specification)\
                .filter_by(name=klass_name)

        for instance in schema_query.all():
            names.append(tuple([
                instance.schema.specification.name,
                instance.schema.specification.title,
                instance.title,
                instance.state.name,
                instance.state.title
                ]))

        return tuple(names)

    def getEnteredDataCount(self, context, klass_name=None, state=None):
        """
        """
        Session = self._datastore.getScopedSession()

        schema_query = Session.query(model.Instance)\
            .join(self._model.instances)\
            .filter(self._model.zid == context.zid)\

        if state:
            schema_query = schema_query \
                .join(model.State)\
                .filter_by(name=state)

        if klass_name:
            schema_query = schema_query \
                .join(model.Schema)\
                .join(model.Specification)\
                .filter_by(name=klass_name)

        return schema_query.count()


    def getEnteredDataOfType(self, context, type):
        """ Get all of the data entered for a context
        """
        Session = self._datastore.getScopedSession()

        instance = Session.query(model.Instance)\
            .join(self._model.instances)\
            .filter(self._model.zid==context.zid)\
            .join(model.Schema)\
            .join(model.Specification)\
            .filter_by(name=type)\
            .first()

        if not instance:
            return None

        return self._datastore.get(instance.title)


    def add_instances(self, context, obj_or_list):
        """ ??!? """
        Session = self._datastore.getScopedSession()
        result = Session.query(self._model).filter_by(zid=context.zid).first()

        for obj in obj_or_list:
            instance = Session.query(model.Instance)\
                .filter_by(title=obj.title)\
                .first()
            result.instances.append(instance)

        transaction.commit()
