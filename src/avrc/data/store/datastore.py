"""
Datastore implementation module as supporting utilities.
"""
from collections import deque as queue
from time import time as currenttime
from datetime import datetime, date, time
import logging

from zope.component import provideUtility
from zope.component import getUtility
from zope.component import queryUtility
from zope.component import adapter
from zope.component.factory import Factory
from zope.interface import implements
from zope.interface import providedBy
from zope.i18nmessageid import MessageFactory
from zope.event import notify
from zope.lifecycleevent import ObjectCreatedEvent
from zope.lifecycleevent import IObjectCreatedEvent
from zope.lifecycleevent import IObjectRemovedEvent
import zope.schema
from zope.schema.fieldproperty import FieldProperty

import sqlalchemy as sa
from sqlalchemy import orm

from avrc.data.store import model
from avrc.data.store import interfaces

_ = MessageFactory(__name__)

log = logging.getLogger(__name__)

_ECHO_ENABLED = False

_DS_FMT = u"<Datastore '%s'>"

def session_name_format(datastore):
    """
    Helper method to format a session name corresponding to the data store.

    Arguments:
        datastore: (object) an object implementing IDatastore
    Returns:
        A string to use as the session utility name.
    """
    return "%s:session" % str(datastore)

def named_session(datastore):
    """
    Evaluates the session being used by the given data store.

    Arguments:
        datastore: (object) an object implementing IDatastore
    Returns:
        A sqlalchemy Session factory.
    """
    return queryUtility(interfaces.ISessionFactory,
                        name=session_name_format(datastore))

def setup_types(datastore):
    """
    Helper method to setup up built-in supported types.

    Arguments:
        datastore: (object) an object implementing IDatastore
    Returns:
        N/A
    """
    rslt = []
    Session = named_session(datastore)
    session = Session()
    types_factory = getUtility(zope.schema.interfaces.IVocabularyFactory,
                               name="avrc.data.store.SupportedTypes")

    for t in list(types_factory()):
        rslt.append(model.Type(
            title=unicode(t.token),
            description=unicode(getattr(t.value, "__doc__", None)),
            ))

    session.add_all(rslt)
    session.commit()

@adapter(interfaces.IDatastore, IObjectCreatedEvent)
def handleDatastoreCreated(datastore, event):
    """
    Triggered when a new DataStore instance is added to a container (i.e.
    when it is added to a site. Essentially, it setups up the database
    back-end.

    Arguments:
        datastore: (object) the newly created object implementing IDatastore
        event: (object) the event object
    Returns:
        N/A
    """
    Session = SessionFactory(bind=sa.create_engine(datastore.dsn,
                                                   echo=_ECHO_ENABLED))

    provideUtility(Session,
                   provides=interfaces.ISessionFactory,
                   name=session_name_format(datastore))

    session = Session()
    model.setup(session.bind)
    setup_types(datastore)

@adapter(interfaces.IDatastore, IObjectRemovedEvent)
def handleDatastoreRemoved(datastore, event):
    """
    Triggered when a new DataStore instance is removed from a container

    Arguments:
        datastore: (object) the removed object implementing IDatastore
        event: (object) the event object
    Returns:
        N/A
    """
    provideUtility(None,
                   provided=interfaces.ISessionFactory,
                   name=session_name_format(datastore))

class SessionFactory(object):
    implements(interfaces.ISessionFactory)

    __doc__ = interfaces.ISessionFactory.__doc__

    __name__ = None

    __parent__ = None

    def __init__(self,
                 autocommit=False,
                 autoflush=True,
                 twophase=False,
                 bind=None,
                 binds=None):
        """
        Our ISessionFactory implementation takes an extra parameter which
        will be the database bindings.

        TODO: (mmartinez) Perhaps make an adapter to extend the functionality
            of z3c.saconfig?
        """
        self.autocommit = autocommit
        self.autoflush = autoflush
        self.twophase = twophase
        self.binds = binds
        self.bind = bind

    def __call__(self):
        Session  = orm.scoped_session(orm.sessionmaker(
            autocommit=self.autocommit,
            autoflush=self.autoflush,
            twophase=self.twophase
            ))

        Session.configure(bind=self.bind, binds=self.binds)

        return Session

    __call__.__doc__ = interfaces.ISessionFactory["__call__"].__doc__

class Datastore(object):
    implements(interfaces.IDatastore)

    __doc__ = interfaces.IDatastore.__doc__

    __name__ = None

    __parent__ = None

    title = FieldProperty(interfaces.IDatastore["title"])

    dsn = FieldProperty(interfaces.IDatastore["dsn"])

    def __init__(self, title, dsn):
        """
        Instantiates the data store implementation. Also notifies listeners
        that this object has been created.

        Arguments:
            title: (str) the name of this data store instance
            dsn: (str) the URI to the data base
        """
        self.title = title
        self.dsn = dsn

        notify(ObjectCreatedEvent(self))

    def __str__(self):
        """
        String representation of this instance
        """
        return _DS_FMT % self.title

    @property
    def schemata(self):
        """A schema manager utility"""
        return interfaces.ISchemaManager(self)

    @property
    def protocols(self):
        """A protocol manager utility"""
        return interfaces.IProtocolManager(self)

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
            key = key.__dsid__
        else:
            raise Exception("The object specified cannot be evaluated into "
                            "a object to search for")

        instance_rslt = session.query(model.Instance)\
                        .filter_by(id=key)\
                        .first()

        return instance_rslt is not None

    has.__doc__ = interfaces.IDatastore["has"].__doc__


    def get(self, key):
        # we're going to use the object as the key (or it's 'name')
        types = getUtility(zope.schema.interfaces.IVocabularyFactory,
                           name="avrc.data.store.SupportedTypes"
                           )()
        Session = named_session(self)
        session = Session()

        if isinstance(key, (str, unicode)):
            key = str(key)
        elif interfaces.IInstance.providedBy(key):
            key = key.__dsid__
        else:
            raise Exception("The object specified cannot be evaluated into "
                            "a object to search for")

        instance_rslt = session.query(model.Instance)\
                        .filter_by(id=key)\
                        .first()

        if instance_rslt is None:
            return None




        # (parent object, corresponding parent db entry, value)
        to_visit = queue([(None, None, None, target)])

        primitive_types = (int, str, unicode, float, bool, date, time, datetime,)

        # Breadth-first pre-order traversal insertion (to keep everything
        # within a single transaction)
        while len(to_visit) > 0:
            (parent_obj, instance_rslt, attr_name, value) = to_visit.popleft()

            # An object, add it's properties to the traversal queue
            if not isinstance(value, primitive_types):
#                if not interfaces.ISchema.providedBy(value):
#                    raise Exception("This object is not going to work out")

                try:
                    provided = list(providedBy(value))
                    (schema_obj,) = provided
                except ValueError as e:
                    raise Exception("Object has multiple inheritance: %s" % e)

                schema_rslt = session.query(model.Schema)\
                              .filter_by(create_date=schema_obj.__version__)\
                              .join(model.Specification)\
                              .filter_by(module=schema_obj.__name__)\
                              .first()

                instance_rslt = model.Instance(
                    schema=schema_rslt,
                    title=u"%s-%d" % (schema_rslt.specification.module,
                                      currenttime()),
                    description=u"Some gibberish"
                    )

                for name, field_obj in zope.schema.getFieldsInOrder(schema_obj):
                    child = getattr(value, name)
                    to_visit.append((value, instance_rslt, name, child,))

            else:

                attribute_rslt = session.query(model.Attribute)\
                                 .filter_by(name=unicode(attr_name))\
                                 .join(model.Schema)\
                                 .filter_by(id=instance_rslt.schema.id)\
                                 .first()

                type_name = attribute_rslt.field.type.title

                if type_name in (u"binary",):
                    Field = model.Binary
                elif type_name in (u"date", u"time", u"datetime"):
                    Field = model.Datetime
                elif type_name in (u"integer",):
                    Field = model.Integer
                elif type_name in (u"object",):
                    Field = model.Object
                elif type_name in (u"real",):
                    Field = model.Real
                elif type_name in (u"text", u"string"):
                    Field = model.String
                elif type_name in (u"selection"):
                    Field = model.Selection
                else:
                    raise Exception("Type '%s' unsupported."  % type_name)

                value_rslt = Field(
                    instance=instance_rslt,
                    attribute=attribute_rslt,
                    value=value
                    )

                session.add(value_rslt)

        session.commit()

    get.__doc__ = interfaces.IDatastore["get"].__doc__

    def put(self, target):
        types = getUtility(zope.schema.interfaces.IVocabularyFactory,
                           name="avrc.data.store.SupportedTypes"
                           )()
        Session = named_session(self)
        session = Session()

        # (parent object, corresponding parent db entry, value)
        to_visit = queue([(None, None, None, target)])

        primitive_types = (int, str, unicode, float, bool, date, time, datetime,)

        # Breadth-first pre-order traversal insertion (to keep everything
        # within a single transaction)
        while len(to_visit) > 0:
            (parent_obj, instance_rslt, attr_name, value) = to_visit.popleft()

            # An object, add it's properties to the traversal queue
            if not isinstance(value, primitive_types):
#                if not interfaces.ISchema.providedBy(value):
#                    raise Exception("This object is not going to work out")

                try:
                    provided = list(providedBy(value))
                    (schema_obj,) = provided
                except ValueError as e:
                    raise Exception("Object has multiple inheritance: %s" % e)

                schema_rslt = session.query(model.Schema)\
                              .filter_by(create_date=schema_obj.__version__)\
                              .join(model.Specification)\
                              .filter_by(module=schema_obj.__name__)\
                              .first()

                instance_rslt = model.Instance(
                    schema=schema_rslt,
                    title=u"%s-%d" % (schema_rslt.specification.module,
                                      currenttime()),
                    description=u"Some gibberish"
                    )

                for name, field_obj in zope.schema.getFieldsInOrder(schema_obj):
                    child = getattr(value, name)
                    to_visit.append((value, instance_rslt, name, child,))

            else:

                attribute_rslt = session.query(model.Attribute)\
                                 .filter_by(name=unicode(attr_name))\
                                 .join(model.Schema)\
                                 .filter_by(id=instance_rslt.schema.id)\
                                 .first()

                type_name = attribute_rslt.field.type.title

                if type_name in (u"binary",):
                    Field = model.Binary
                elif type_name in (u"date", u"time", u"datetime"):
                    Field = model.Datetime
                elif type_name in (u"integer",):
                    Field = model.Integer
                elif type_name in (u"object",):
                    Field = model.Object
                elif type_name in (u"real",):
                    Field = model.Real
                elif type_name in (u"text", u"string"):
                    Field = model.String
                elif type_name in (u"selection"):
                    Field = model.Selection
                else:
                    raise Exception("Type '%s' unsupported."  % type_name)

                value_rslt = Field(
                    instance=instance_rslt,
                    attribute=attribute_rslt,
                    value=value
                    )

                session.add(value_rslt)

        session.commit()

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
            key = key.__dsid__
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
            key = key.__dsid__
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

DatastoreFactory = Factory(
    Datastore,
    title=_(u"Datastore implementation factory."),
    description=_(u"Creates an instance of a datastore implementation object. "
                   "Also notifies listeners of this creation.")
    )
