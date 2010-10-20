""" Datastore implementation module as supporting utilities.
"""
from collections import deque as queue
from time import time as currenttime
from datetime import datetime, date
import logging

from zope.component import provideUtility
from zope.component import getUtility
from zope.component import adapter
from zope.component.factory import Factory
from zope.interface import implements
from zope.interface import providedBy
from zope.interface import directlyProvides
from zope.event import notify
from zope.lifecycleevent import ObjectCreatedEvent
from zope.lifecycleevent import IObjectCreatedEvent
from zope.lifecycleevent import IObjectRemovedEvent
import zope.schema
from zope.schema.interfaces import IVocabulary
from zope.schema.fieldproperty import FieldProperty
import zope.interface

from z3c.saconfig import named_scoped_session

from avrc.data.store import MessageFactory as _
from avrc.data.store import model
from avrc.data.store import interfaces

import transaction

log = logging.getLogger(__name__)

_ECHO_ENABLED = False

_DS_FMT = u"<Datastore '%s'>"

def session_name_format(datastore):
    """ Helper method to format a session name corresponding to the data store.

        Arguments:
            datastore: (object) an object implementing IDatastore
        Returns:
            A string to use as the session utility name.
    """
    return "%s:session" % str(datastore)

def named_session(datastore):
    """ Evaluates the session being used by the given data store.

        Arguments:
            datastore: (object) an object implementing IDatastore
        Returns:
            A sqlalchemy Session factory.
    """
    return named_scoped_session(datastore.session_name)
#
#    return datastore.getSession()

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

@adapter(interfaces.IDatastore, IObjectCreatedEvent)
def handleDatastoreCreated(datastore, event):
    """ Triggered when a new DataStore instance is added to a container (i.e.
        when it is added to a site. Essentially, it setups up the database
        back-end.

        Arguments:
            datastore: (object) the newly created object implementing IDatastore
            event: (object) the event object
        Returns:
            N/A
    """
#    if str(datastore.dsn).find('sqlite') > -1:
#        Session = SessionFactory(bind=sa.create_engine(datastore.dsn,
#                                           echo=_ECHO_ENABLED))
#    else:
#        Session = SessionFactory(bind=sa.create_engine(datastore.dsn,
#                                           echo=_ECHO_ENABLED, pool_size=100, max_overflow=10))
#
#
#    sm = getSiteManager(datastore)
#    sm.registerUtility(Session,
#                       interfaces.ISessionFactory,
#                       session_name_format(datastore))
#    Session =
#    session = Session()
    model.setup(named_session(datastore).bind)
#    session.close()
#
    setup_types(datastore)


@adapter(interfaces.IDatastore, IObjectRemovedEvent)
def handleDatastoreRemoved(datastore, event):
    """ Triggered when a new DataStore instance is removed from a container

        Arguments:
            datastore: (object) the removed object implementing IDatastore
            event: (object) the event object
        Returns:
            N/A
    """
    # TODO do ti for the site
    provideUtility(None,
                   interfaces.ISessionFactory,
                   session_name_format(datastore))

#from persistent import Persistent
#
#class SessionFactory(Persistent):
#    implements(interfaces.ISessionFactory)
#
#    __doc__ = interfaces.ISessionFactory.__doc__
#
#    __name__ = None
#
#    __parent__ = None
#
#    def __init__(self,
#                 autocommit=False,
#                 autoflush=True,
#                 twophase=False,
#                 bind=None,
#                 binds=None):
#        """
#        Our ISessionFactory implementation takes an extra parameter which
#        will be the database bindings.
#
#        TODO: (mmartinez) Perhaps make an adapter to extend the functionality
#            of z3c.saconfig?
#        """
#        self.autocommit = autocommit
#        self.autoflush = autoflush
#        self.twophase = twophase
#        self.binds = binds
#        self.bind = bind
#        super(Persistent, self).__init__()
#
#    def __call__(self):
#        Session  = orm.scoped_session(orm.sessionmaker(
#            autocommit=self.autocommit,
#            autoflush=self.autoflush,
#            twophase=self.twophase
#            ))
#
#        Session.configure(bind=self.bind, binds=self.binds)
#        if Session is None:
#            raise Exception('wtf??')
#        return Session
#
#    __call__.__doc__ = interfaces.ISessionFactory["__call__"].__doc__

class Instance(object):
    implements(interfaces.IInstance)

    __doc__ = interfaces.IInstance.__doc__

    __id__ = None

    __schema__ = None

    title = None

    description = None

    def __str__(self):
        return "<Instance: '%s'; implements: '%s'>" \
                % (self.title, self.__schema__.__name__)

class Datastore(object):
    implements(interfaces.IDatastore)

    __doc__ = interfaces.IDatastore.__doc__

    __name__ = None

    __parent__ = None

    title = FieldProperty(interfaces.IDatastore["title"])

    dsn = FieldProperty(interfaces.IDatastore["dsn"])

    session_name = FieldProperty(interfaces.IDatastore["session_name"])

    def __init__(self, title, dsn=None, session_name=None):
        """ Instantiates the data store implementation. Also notifies listeners
            that this object has been created.

            Arguments:
                title: (str) the name of this data store instance
                dsn: (str) the URI to the data base
        """
        self.title = title
        self.dsn = dsn
        self.session_name = session_name

        notify(ObjectCreatedEvent(self))

    def __str__(self):
        """ String representation of this instance """
        return _DS_FMT % self.title

#    def getSession(self):
#        sm = getSiteManager(self)
#        session = sm.queryUtility(interfaces.ISessionFactory, session_name_format(self))
#        if session is not None:
#            return sm.queryUtility(interfaces.ISessionFactory, session_name_format(self))
#        else:
#            if str(self.dsn).find('sqlite') > -1:
#                Session = SessionFactory(bind=sa.create_engine(self.dsn,
#                                                   echo=_ECHO_ENABLED))
#            else:
#                Session = SessionFactory(bind=sa.create_engine(self.dsn,
#                                                   echo=_ECHO_ENABLED, pool_size=100, max_overflow=10))
#            sm.registerUtility(Session,
#                       interfaces.ISessionFactory,
#                       session_name_format(self))
#        return  sm.queryUtility(interfaces.ISessionFactory, session_name_format(self))

    @property
    def search(self):
        """ """
        from avrc.data.store.search import SearchMonkey
        return SearchMonkey(self)

    @property
    def schemata(self):
        """ A schema manager utility """
        return interfaces.ISchemaManager(self)

    @property
    def domains(self):
        """ A protocol manager utility """
        return interfaces.IDomainManager(self)

    @property
    def subjects(self):
        """ A protocol manager utility """
        return interfaces.ISubjectManager(self)

    @property
    def protocols(self):
        """ A protocol manager utility """
        return interfaces.IProtocolManager(self)

    @property
    def enrollments(self):
        """ A protocol manager utility """
        return interfaces.IEnrollmentManager(self)

    @property
    def visits(self):
        """ A protocol manager utility """
        return interfaces.IVisitManager(self)

    @property
    def specimen(self):
        """ A specimen manager utility """
        return interfaces.ISpecimenManager(self)

    @property
    def aliquot(self):
        """ A specimen manager utility """
        return interfaces.IAliquotManager(self)

    def keys(self):
        # This method will remain unimplemented as it doesn't really make sense
        # to return every single key in the data store.
        pass

    keys.__doc__ = interfaces.IDatastore["keys"].__doc__

    def has(self, key):
        # we're going to use the object as the key (or it's 'name')
        Session = named_session(self)
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
        types = getUtility(IVocabulary, "avrc.data.store.Types")
        Session = named_session(self)
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
                    raise Exception("Using nested objects, not supported yet...")
                    instance_obj = Instance()
                    # TOD fix this...
                    setattr(instance_obj, "__id__", None)
                    setattr(parent_obj, str(attribute_rslt.name), instance_obj)
                    #to_visit.append((object_rslt.value, instance_obj, None, None,))
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
        types = getUtility(IVocabulary, "avrc.data.store.Types")
        Session = named_session(self)
        session = Session()

        is_update = False

        # (parent object, corresponding db entry, prop name, raw value)
        # in this case, the target isn't assign to or contained in anything.
        to_visit = queue([(None, None, None, target)])

#        primitive_types = (int, str, unicode, float, bool, date, time,
#                           datetime, list)

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
        Session = named_session(self)
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
        Session = named_session(self)
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
        elif target.extends(zope.interface.Interface):
            iface = target
        else:
            raise Exception("%s will not be found" % target)

        obj = Instance()
        directlyProvides(obj, iface)

        setattr(obj, "__schema__", iface)

        for name, field_obj in zope.schema.getFieldsInOrder(iface):
#            setattr(obj, name, FieldProperty(field_obj))
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

    spawn.__doc__ = interfaces.IDatastore["spawn"].__doc__

DatastoreFactory = Factory(
    Datastore,
    title=_(u"Datastore implementation factory."),
    description=_(u"Creates an instance of a datastore implementation object. "
                  u"Also notifies listeners of this creation.")
    )
