""" Defines several useful manager base classes.
"""

from zope.deprecation import deprecate

from avrc.data.store import model


class AbstractDatastoreManager(object):
    """ Base class for all manager types.
    """

    def __init__(self, datastore):
        self._datastore = datastore

    def keys(self):
        raise NotImplementedError

    def has(self, key):
        raise NotImplementedError

    def get(self, key):
        raise NotImplementedError

    def purge(self, key):
        raise NotImplementedError

    def retire(self,key):
        raise NotImplementedError

    def restore(self, key):
        raise NotImplementedError

    def put(self, target):
        raise NotImplementedError


class AbstractDatastoreConventionalManager(AbstractDatastoreManager):
    """ See `IConventionalManager`
    """

    _model = None

    _type = None


    def putProperties(self, rslt, source):
        raise NotImplementedError("Subclasses must implement putProperties")


    def get(self, key):
        """ See `IConventionalManager.get`
        """
        Session = self._datastore.getScopedSession()
        entry = Session.query(self._model).filter_by(zid=key).first()
        result = None

        if entry is not None:
            result = self._type()
            self.putProperties(result, entry)

        return result


    def put(self, source):
        """ See `IConventionalManager.put`
        """
        Session = self._datastore.getScopedSession()
        entry = Session.query(self._model).filter_by(zid=source.zid).first()

        if entry is None:
            entry = self._model(zid=source.zid)

        # TODO: (mmartinez) This method should be able to figure it out as
        # opposed to having each class define their mapping. It all depends
        # on proper Interface setup.
        self.putProperties(entry, source)

        if not entry.id:
            Session.add(entry)
        else:
            Session.flush()

        Session.flush()
        return source


    def retire(self, source):
        """ See `IConventionalManager.retire`
        """
        Session = self._datastore.getScopedSession()
        rslt = Session.query(self._model).filter_by(zid=source.zid).first()
        if rslt is not None:
            rslt.is_active = False
            Session.flush()
        Session.flush()


    def purge(self, source):
        """ See `IConventionalManager.purge`
        """
        Session = self._datastore.getScopedSession()
        rslt = Session.query(self._model).filter_by(zid=source.zid).first()
        if rslt is not None:
            Session.remove(rslt)
        Session.flush()


    def keys(self):
        """ See `IConventionalManager.keys`
        """
        Session = self._datastore.getScopedSession()
        query = Session.query(self._model.zid).filter_by(is_active=True)
        return [zid for zid in query.all()]


class AbstractEAVContainerManager(AbstractDatastoreConventionalManager):
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
            .filter(self._model.zid == context.zid)\
            .join(model.Schema)\
            .join(model.Specification)\
            .filter_by(name=type)\
            .first()

        if not instance:
            return None

        return self._datastore.get(instance.title)


    def addInstances(self, context, values):
        """ Associates EAV values to a context.
        """
        Session = self._datastore.getScopedSession()


        if not isinstance(values, (list, tuple)):
            values = [values]

        for value in values:
            self._datastore.put(value)

        result = Session.query(self._model).filter_by(zid=context.zid).first()

        for value in values:
            instance = Session.query(model.Instance)\
                .filter_by(title=value.title)\
                .first()

            result.instances.append(instance)

        Session.flush()

    @deprecate('add_instances() is deprecated, use addInstances()')
    def add_instances(self, context, obj_or_list):
        """ See `addInstances`
        """
        return self.addInstances(context, obj_or_list)
