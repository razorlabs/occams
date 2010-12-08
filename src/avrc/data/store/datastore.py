""" Datastore implementation module and supporting utilities.
"""
from collections import deque as queue
from time import time as currenttime
from datetime import date
from datetime import datetime

import transaction
from zope.component import getUtility
from zope.component.factory import Factory
from zope.deprecation import deprecate
import zope.interface
from zope.interface import implements
from zope.interface import providedBy
from zope.interface import directlyProvides
import zope.schema
from zope.schema.fieldproperty import FieldProperty

import z3c.saconfig

from avrc.data.store import MessageFactory as _
from avrc.data.store import Logger as log
from avrc.data.store import interfaces
from avrc.data.store import model

class Datastore(object):
    implements(interfaces.IDatastore)

    __doc__ = interfaces.IDatastore.__doc__

    # hidden session name, don't want anyone messing with it
    _session = FieldProperty(interfaces.IDatastore["session"])

    def __init__(self, session=u"", **kw):
        """ Instantiates the data store implementation. Also notifies listeners
            that this object has been created.

            Arguments:
                dsn: (str) the URI to the data base
        """
        if "session_name" in kw:
            # for legacy support
            session = kw["session_name"]

        self._session = session
        model.setup(self.getScopedSession().bind)
        setup_types(self)

    def __str__(self):
        """ String representation of this instance """
        return u"<Datastore('%s')>" % self._session

    def getScopedSession(self):
        return z3c.saconfig.named_scoped_session(self._session)

    def getManager(self, iface):
        return iface(self)

    getManager.__doc__ = interfaces.IDatastore["getManager"].__doc__

    def getAliquotManager(self):
        return self.getManager(interfaces.IAliquotManager)

    getAliquotManager.__doc__ = \
        interfaces.IDatastore["getAliquotManager"].__doc__

    def getSpecimenManager(self):
        return self.getManager(interfaces.ISpecimenManager)

    getSpecimenManager.__doc__ = \
        interfaces.IDatastore["getSpecimenManager"].__doc__

    def getDomainManager(self):
        return self.getManager(interfaces.IDomainManager)

    getDomainManager.__doc__ = \
        interfaces.IDatastore["getDomainManager"].__doc__

    def getEnrollmentManager(self):
        return self.getManager(interfaces.IEnrollmentManager)

    getDomainManager.__doc__ = \
        interfaces.IDatastore["getDomainManager"].__doc__

    def getProtocolManager(self):
        return self.getManager(interfaces.IProtocolManager)

    getProtocolManager.__doc__ = \
        interfaces.IDatastore["getProtocolManager"].__doc__

    def getSchemaManager(self):
        return self.getManager(interfaces.ISchemaManager)

    getSchemaManager.__doc__ = \
        interfaces.IDatastore["getSchemaManager"].__doc__

    def getSubjectManager(self):
        return self.getManager(interfaces.ISubjectManager)

    getSubjectManager.__doc__ = \
        interfaces.IDatastore["getSubjectManager"].__doc__

    def getVisitManager(self):
        return self.getManager(interfaces.IVisitManager)

    getVisitManager.__doc__ = \
        interfaces.IDatastore["getVisitManager"].__doc__

    def getDrugManager(self):
        return self.getManager(interfaces.IDrugManager)

    getDrugManager.__doc__ = \
        interfaces.IDatastore["getDrugManager"].__doc__

    def getMedicationManager(self):
        return self.getManager(interfaces.IMedicationManager)

    getMedicationManager.__doc__ = \
        interfaces.IDatastore["getMedicationManager"].__doc__

    def getSymptomManager(self):
        return self.getManager(interfaces.ISymptomManager)

    getSymptomManager.__doc__ = \
        interfaces.IDatastore["getSymptomManager"].__doc__

    def getPartnerManager(self):
        return self.getManager(interfaces.IPartnerManager)

    getPartnerManager.__doc__ = \
        interfaces.IDatastore["getPartnerManager"].__doc__




    @property
    @deprecate("Use getSchemaManager() instead of schemata")
    def schemata(self):
        return self.getSchemaManager()

    @property
    @deprecate("Use getDomainManager() instead of domains")
    def domains(self):
        return self.getDomainManager()

    @property
    @deprecate("Use getSubjectManager() instead of subjects")
    def subjects(self):
        return self.getSubjectManager()

    @property
    @deprecate("Use getProtocolManager() instead of protocols")
    def protocols(self):
        return self.getProtocolManager()

    @property
    @deprecate("Use getEnrollmentManager() instead of enrollments")
    def enrollments(self):
        return self.getEnrollmentManager()

    @property
    @deprecate("Use getVisitManager() instead of visits")
    def visits(self):
        return self.getVisitManager()

    @property
    @deprecate("Use getSpecimenManager() instead of specimen")
    def specimen(self):
        return self.getSpecimenManager()

    @property
    @deprecate("Use getAliquotManager() instead of aliquot")
    def aliquot(self):
        return self.getAliquotManager()

    def keys(self):
        # This method will remain unimplemented as it doesn't really make sense
        # to return every single key in the data store.
        pass

    keys.__doc__ = interfaces.IDatastore["keys"].__doc__

    def has(self, key):
        Session = self.getScopedSession()
        session = Session()

        # we're going to use the object as the key (or it's 'name')
        if isinstance(key, (str, unicode)):
            key = str(key)
        elif interfaces.IInstance.providedBy(key):
            key = key.__id__
        else:
            raise Exception("The object specified cannot be evaluated into "
                            "a object to search for")

        instance_rslt = session.query(model.Instance)\
                        .filter_by(id=key)\
                        .first()

        return instance_rslt is not None

    has.__doc__ = interfaces.IDatastore["has"].__doc__

    def get(self, key):
        # Since the object doesn't have any dependencies on it's data, we're
        # just going to do another Breadth-first traversal
        #
        # TODO: (mmartinez) get by title as well, currently only works
        #    by id....
        #
        # TODO: (mmartinez) objects come back without their interfaces currently
        #

        # we're going to use the object as the key (or it's 'name')
        Session = self.getScopedSession()
        session = Session()

        searchkw = {}
        if isinstance(key, (str, unicode)):
            searchkw = dict(title=unicode(key))
        elif isinstance(key, (int, long)):
            searchkw = dict(id=int(key))
        elif interfaces.IInstance.providedBy(key):
            if key.__id__:
                searchkw = dict(id=int(key.__id__))
            else:
                searchkw = dict(title=unicode(key.title))
        else:
            raise Exception("The object specified cannot be evaluated into "
                            "a object to search for")

        instance_rslt = session.query(model.Instance)\
                        .filter_by(**searchkw)\
                        .first()

        if instance_rslt is None:
            return None


        key = (instance_rslt.schema.specification.name,
               instance_rslt.schema.create_date,)

        iface = self.schemata.get(key)
        instance_obj = self.spawn(iface)
        setattr(instance_obj, "__id__", instance_rslt.id)
        setattr(instance_obj, "title", str(instance_rslt.title))
        setattr(instance_obj, "__schema__", iface)

        # (parent object, parent db entry, prop name, value)
        to_visit = queue([(instance_obj, instance_rslt, None, None)])

        while len(to_visit) > 0:
            (parent_obj, instance_rslt, attr_name, value) = to_visit.popleft()

            for attribute_rslt in instance_rslt.schema.attributes:

                type_name = attribute_rslt.field.type.title

                if type_name in (u"binary",):
                    Model = model.Binary
                elif type_name in (u"date", u"time", u"datetime"):
                    Model = model.Datetime
                elif type_name in (u"integer", u"boolean"):
                    Model = model.Integer
                elif type_name in (u"real",):
                    Model = model.Real
                elif type_name in (u"object",):
                    Model = model.Object
                elif type_name in (u"text", u"string"):
                    Model = model.String
                elif type_name in (u"selection"):
                    Model = model.Selection
                else:
                    raise Exception("Type '%s' unsupported."  % type_name)

                value_q = session.query(Model)\
                                .filter_by(instance=instance_rslt)\
                                .filter_by(attribute=attribute_rslt)\

                value = None

                if type_name in (u"object",):
                    # TODO fix this...
                    raise Exception("Using nested objects, not supported yet...")
                else:
                    # Sanity check: if there are no values in the data store,
                    # this 'should' result in an empty list OR a None value
                    # which is OK.
                    if attribute_rslt.field.is_list:
                        # a little more processing for selections...
                        if type_name == u"selection":
                            # it's a term relation, relations also have a field
                            # named value...
                            value = [v.value.value for v in value_q.all()]
                        else:
                            value = [v.value for v in value_q.all()]
                    else:
                        value_rslt = value_q.first()

                        if value_rslt:
                            # a little more processing for selections...
                            if type_name == u"selection":
                                value = value_rslt.value.value
                            else:
                                #
                                # TODO need to typecast if necessary
                                #
                                value = value_rslt.value

                    setattr(parent_obj, str(attribute_rslt.name), value)

        return instance_obj

    get.__doc__ = interfaces.IDatastore["get"].__doc__

    def put(self, target):
        Session = self.getScopedSession()
        session = Session()

        is_update = False

        # (parent object, corresponding db entry, prop name, raw value)
        # in this case, the target isn't assign to or contained in anything.
        to_visit = queue([(None, None, None, target)])

        # Breadth-first pre-order traversal insertion (to keep everything
        # within a single transaction)
        while len(to_visit) > 0:
            (parent_obj, parent_rslt, attr_name, value) = to_visit.popleft()

            # we don't want NULL/NIL/None value in the datastore
            if value is None:
                continue

            # An object, add it's properties to the traversal queue
            if interfaces.IInstance.providedBy(value):
#                if not interfaces.Schema.providedBy(value):
#                    raise Exception("This object is not going to work out")

                schema_obj = list(providedBy(value))[0]

                if value.title:
                    instance_rslt = session.query(model.Instance)\
                                    .filter_by(title=value.title)\
                                    .first()
                    is_update = True
                else:
                    schema_rslt = session.query(model.Schema)\
                                  .filter_by(create_date=schema_obj.__version__)\
                                  .join(model.Specification)\
                                  .filter_by(name=schema_obj.__name__)\
                                  .first()

                    instance_rslt = model.Instance(
                        schema=schema_rslt,
                        title=u"%s-%f" % (schema_rslt.specification.name,
                                          currenttime()),
                        description=u""
                        )

                    session.add(instance_rslt)
                    session.flush()

                    value.title = instance_rslt.title
                    setattr(value, "__id__", instance_rslt.id)

                for name, field_obj in zope.schema.getFieldsInOrder(schema_obj):
                    # don't do getattr as this will potentially get the
                    # FieldProperty object (if present)
                    child = getattr(value, name, None)
                    to_visit.append((value, instance_rslt, name, child,))

            else:

                attribute_rslt = session.query(model.Attribute)\
                                 .filter_by(name=unicode(attr_name))\
                                 .join(model.Schema)\
                                 .filter_by(id=parent_rslt.schema.id)\
                                 .first()

                type_name = attribute_rslt.field.type.title

                if type_name in (u"binary",):
                    Model = model.Binary
                elif type_name in (u"date", u"time", u"datetime",):
                    Model = model.Datetime
                elif type_name in (u"boolean",):
                    Model = model.Integer
                    if attribute_rslt.field.is_list:
                        value = map(int, value)
                    else:
                        value = int(value)
                elif type_name in (u"integer",):
                    Model = model.Integer
                elif type_name in (u"object",):
                    Model = model.Object
                elif type_name in (u"real",):
                    Model = model.Real
                elif type_name in (u"text", u"string",):
                    Model = model.String
                elif type_name in (u"selection", ):
                    Model = model.Selection
                else:
                    raise Exception("Type '%s' unsupported."  % type_name)

                # convert to list (for convenience in iterating rather than
                # checking)
                if not attribute_rslt.field.is_list:
                    value = [value]

                # selections are actually just references to a term
                if type_name == u"selection":
                    rslt_values = []
                    for term_rslt in attribute_rslt.field.vocabulary.terms:
                        if term_rslt.value in value:
                            rslt_values.append(term_rslt)

                    value = rslt_values

                # delete the whole list, too complicated to update for now
                if is_update and attribute_rslt.field.is_list:
                    list_rslt = session.query(Model)\
                                .filter_by(instance=parent_rslt)\
                                .filter_by(attribute=attribute_rslt)\
                                .all()

                    for item_rslt in list_rslt:
                        session.delete(item_rslt)

                for v in value:
                    value_rslt = None

                    if is_update and not attribute_rslt.field.is_list:
                        value_rslt = session.query(Model)\
                                        .filter_by(instance=parent_rslt)\
                                        .filter_by(attribute=attribute_rslt)\
                                        .first()

                    if value_rslt is None or attribute_rslt.field.is_list:
                        session.add(Model(
                            instance=parent_rslt,
                            attribute=attribute_rslt,
                            value=v
                            ))
                    else:
                        value_rslt.value = v

        transaction.commit()

        return target

    put.__doc__ = interfaces.IDatastore["put"].__doc__

    def purge(self, key):
        raise NotImplementedError()

    purge.__doc__ = interfaces.IDatastore["purge"].__doc__

    def retire(self, key):
        # we're going to use the object as the key (or it's 'name')
        Session = self.getScopedSession()
        session = Session()

        if isinstance(key, (str, unicode)):
            key = str(key)
        elif interfaces.IInstance.providedBy(key):
            key = key.__id__
        else:
            raise Exception("The object specified cannot be evaluated into "
                            "a object to search for")

        instance_rslt = session.query(model.Instance)\
                        .filter_by(id=key)\
                        .first()

        if instance_rslt:
            instance_rslt.is_active = False
            session.flush()

        return instance_rslt is not None

    retire.__doc__ = interfaces.IDatastore["retire"].__doc__

    def restore(self, key):
        # we're going to use the object as the key (or it's 'name')
        Session = self.getScopedSession()
        session = Session()

        if isinstance(key, (str, unicode)):
            key = str(key)
        elif interfaces.IInstance.providedBy(key):
            key = key.__id__
        else:
            raise Exception("The object specified cannot be evaluated into "
                            "a object to search for")

        instance_rslt = session.query(model.Instance)\
                        .filter_by(id=key)\
                        .first()

        if instance_rslt:
            instance_rslt.is_active = True
            session.flush()

        return instance_rslt is not None

    restore.__doc__ = interfaces.IDatastore["restore"].__doc__

    def spawn(self, target, **kw):
        if isinstance(target, (str, unicode)):
            iface = self.schemata.get(target)
        else:
            iface = target
        return spawnObject(iface, **kw)

    spawn.__doc__ = interfaces.IDatastore["spawn"].__doc__

DatastoreFactory = Factory(
    Datastore,
    title=_(u"Datastore implementation factory."),
    description=_(u"Creates an instance of a datastore implementation object. "
                  u"Also notifies listeners of this creation.")
    )

@deprecate("Use datastore's getScopedSession() instead of named_session()")
def named_session(datastore):
    """ Evaluates the session being used by the given data store.

        Arguments:
            datastore: (object) an object implementing IDatastore
        Returns:
            A sqlalchemy Session factory.
    """
    return datastore.getScopedSession()

def spawnObject(iface, **kw):
    """ Spawns "anonymous" objects from interface specifications.

        Arguments:
            iface: (object) a zope Interface or child class
            **kw: (dict) additional arguments for the instantiated object
    """
    if not iface.extends(zope.interface.Interface):
        raise Exception("%s will not be found" % iface)

    class Instance(object):
        implements(interfaces.IInstance)
        __id__ = None
        __schema__ = None
        title = None
        description = None

        def __str__(self):
            return u"<Instance: '%s'; implements: '%s'>" \
                    % (self.title, self.__schema__.__name__)

    obj = Instance()
    directlyProvides(obj, iface)

    setattr(obj, "__schema__", iface)

    for name, field_obj in zope.schema.getFieldsInOrder(iface):
        # TODO: figure out how to use FieldProperty with this
        setattr(obj, name, None)

        if field_obj.__class__ is zope.schema.Datetime:
            value = kw.get(name, datetime.now())
        elif field_obj.__class__ is zope.schema.Date:
            value = kw.get(name, date.today())
        else:
            value = kw.get(name)

        if name in kw:
            obj.__dict__[name] = value

    return obj

def setup_types(datastore):
    """ Helper method to setup up built-in supported types.

        Arguments:
            datastore: (object) an object implementing IDatastore
        Returns:
            N/A
    """
    rslt = []
    Session = named_session(datastore)
    session = Session()

    types = getUtility(zope.schema.interfaces.IVocabulary,
                       "avrc.data.store.Types")

    for t in list(types):
        num = session.query(model.Type)\
                .filter_by(title=unicode(t.token))\
                .count()

        if not num:
            rslt.append(model.Type(
                title=unicode(t.token),
                description=unicode(getattr(t.value, "__doc__", None)),
                ))

    if rslt:
        session.add_all(rslt)
        transaction.commit()
