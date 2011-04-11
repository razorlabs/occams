""" Datastore implementation module and supporting utilities.
"""
from collections import deque as queue
from time import time as currenttime
from datetime import date
from datetime import datetime

from zope.component import getUtility
from zope.component.factory import Factory

from zope.deprecation import deprecate
import zope.interface
from zope.interface import implements
from zope.interface import classProvides
from zope.interface import providedBy
from zope.interface import directlyProvides
import zope.schema

import z3c.saconfig

import sqlalchemy.types
from sqlalchemy.sql.expression import cast

from avrc.data.store import MessageFactory as _
from avrc.data.store import Logger as log
from avrc.data.store import interfaces
from avrc.data.store import model



# Where the types are stored
name_model_map = dict(
    integer=model.Integer,
    string=model.String,
    text=model.String,
    boolean=model.Integer,
    real=model.Real,
    date=model.Datetime,
    datetime=model.Datetime,
    time=model.Datetime
    )

# What the types are cast to when queried
name_dbtype_map = dict(
    integer=sqlalchemy.types.Integer,
    string=sqlalchemy.types.Unicode,
    text=sqlalchemy.types.UnicodeText,
    boolean=sqlalchemy.types.Boolean,
    real=sqlalchemy.types.Float,
    date=sqlalchemy.types.Date,
    datetime=sqlalchemy.types.DateTime,
    time=sqlalchemy.types.Time,
    )

# What the types are cast to when stored
name_coalesce_map = dict(
    integer=int,
    string=unicode,
    text=unicode,
    boolean=int,
    real=float,
    )


class Datastore(object):
    """ Datastore Implementation
        See `IDatastore`
        See `IDatastoreFactory`
    """
    classProvides(interfaces.IDatastoreFactory)
    implements(interfaces.IDatastore)

    def __init__(self, session):
        self._session = session
        model.setup(self.getScopedSession().bind)
        setup_types(self)


    def __str__(self):
        """ String representation of this instance
        """
        return u'<Datastore Session(\'%s\')>' % str(self._session)


    def getScopedSession(self):
        return z3c.saconfig.named_scoped_session(self._session)


    def getManager(self, iface):
        return iface(self)


    def getAliquotManager(self):
        return self.getManager(interfaces.IAliquotManager)


    def getSpecimenManager(self):
        return self.getManager(interfaces.ISpecimenManager)


    def getDomainManager(self):
        return self.getManager(interfaces.IDomainManager)


    def getEnrollmentManager(self):
        return self.getManager(interfaces.IEnrollmentManager)


    def getProtocolManager(self):
        return self.getManager(interfaces.IProtocolManager)


    def getSchemaManager(self):
        return self.getManager(interfaces.ISchemaManager)


    def getSubjectManager(self):
        return self.getManager(interfaces.ISubjectManager)


    def getVisitManager(self):
        return self.getManager(interfaces.IVisitManager)


    def getDrugManager(self):
        return self.getManager(interfaces.IDrugManager)


    def getMedicationManager(self):
        return self.getManager(interfaces.IMedicationManager)


    def getSymptomManager(self):
        return self.getManager(interfaces.ISymptomManager)


    def getPartnerManager(self):
        return self.getManager(interfaces.IPartnerManager)


    @property
    @deprecate('Use getSchemaManager() instead of schemata')
    def schemata(self):
        return self.getSchemaManager()


    @property
    @deprecate('Use getDomainManager() instead of domains')
    def domains(self):
        return self.getDomainManager()


    @property
    @deprecate('Use getSubjectManager() instead of subjects')
    def subjects(self):
        return self.getSubjectManager()


    @property
    @deprecate('Use getProtocolManager() instead of protocols')
    def protocols(self):
        return self.getProtocolManager()


    @property
    @deprecate('Use getEnrollmentManager() instead of enrollments')
    def enrollments(self):
        return self.getEnrollmentManager()


    @property
    @deprecate('Use getVisitManager() instead of visits')
    def visits(self):
        return self.getVisitManager()


    @property
    @deprecate('Use getSpecimenManager() instead of specimen')
    def specimen(self):
        return self.getSpecimenManager()


    @property
    @deprecate('Use getAliquotManager() instead of aliquot')
    def aliquot(self):
        return self.getAliquotManager()


    def keys(self):
        # This method will remain unimplemented as it doesn't really make sense
        # to return every single key in the data store.
        pass


    def has(self, key):
        Session = self.getScopedSession()

        # we're going to use the object as the key (or it's 'name')
        if isinstance(key, basestring):
            key = str(key)
        elif interfaces.IInstance.providedBy(key):
            key = key.__id__
        else:
            raise Exception('The object specified cannot be evaluated into '
                            'a object to search for')

        return 0 < Session.query(model.Instance).filter_by(id=key).count()


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

        filter = None

        if isinstance(key, basestring):
            filter = dict(title=key)
        elif isinstance(key, (int, long)):
            filter = dict(id=key)
        else:
            raise Exception('The item \'%s\' cannot be searched for.' % key)

        instance_rslt = Session.query(model.Instance).filter_by(**filter).first()

        if instance_rslt is None:
            return None

        key = (instance_rslt.schema.specification.name,
               instance_rslt.schema.create_date)

        schema = self.getSchemaManager().get(key)
        instance_obj = self.spawn(schema)

        setattr(instance_obj, '__id__', instance_rslt.id)
        setattr(instance_obj, 'title', str(instance_rslt.title))
        setattr(instance_obj, '__schema__', schema)
        setattr(instance_obj, '__state__', instance_rslt.state.name)

        # (parent object, parent db entry, prop name, value)
        to_visit = queue([(instance_obj, instance_rslt, None, None)])

        while len(to_visit) > 0:
            (parent_obj, instance_rslt, attr_name, value) = to_visit.popleft()

            for attribute_rslt in instance_rslt.schema.attributes:

                # Worflow state is deprecated and should be ignored
                if attribute_rslt.name == u'state':
                    continue

                type_name = attribute_rslt.field.type.title

                if type_name in (u'object',):
                    raise Exception('Using nested objects, not supported yet...')
                elif type_name not in name_model_map:
                    raise Exception('Type \'%s\' unsupported.' % type_name)

                Model = name_model_map[type_name]
                column = cast(Model.value, name_dbtype_map[type_name])

                value_rslt = Session.query(column)\
                    .filter_by(instance=instance_rslt)\
                    .filter_by(attribute=attribute_rslt)\
                    .all()

                if value_rslt is None:
                    value = None
                else:
                    value = [v for (v,) in value_rslt]

                    if len(value) <= 0:
                        value = None
                    else:
                        if not attribute_rslt.field.is_list:
                            value = value.pop()


                setattr(parent_obj, str(attribute_rslt.name), value)

        return instance_obj


    def put(self, target):
        Session = self.getScopedSession()

        # (parent object, corresponding db entry, prop name, raw value)
        # in this case, the target isn't assign to or contained in anything.
        to_visit = queue([(None, None, None, target)])

        # Breadth-first pre-order traversal insertion (to keep everything
        # within a single transaction)
        while len(to_visit) > 0:
            (parent_obj, parent_rslt, attr_name, value) = to_visit.popleft()

            # Worflow state is deprecated and should be ignored
            if attr_name == u'state':
                continue

            # We have an object, add it's properties to the traversal queue
            if interfaces.IInstance.providedBy(value):

                schema_obj = list(providedBy(value))[0]

                state_query = Session.query(model.State)

                if value.getState() is None:
                    state_query = state_query.filter_by(is_default=True)
                else:
                    state_query = state_query.filter_by(name=value.getState())

                state_rslt = state_query.first()

                if value.title:
                    instance_rslt = Session.query(model.Instance)\
                        .filter_by(title=value.title)\
                        .first()
                    instance_rslt.state = state_rslt
                else:
                    schema_rslt = Session.query(model.Schema)\
                        .filter_by(create_date=schema_obj.__version__)\
                        .join(model.Specification)\
                        .filter_by(name=schema_obj.__name__)\
                        .first()

                    instance_rslt = model.Instance(
                        schema=schema_rslt,
                        title=u'%s-%f' % (schema_rslt.specification.name,
                                          currenttime()),
                        description=u'',
                        state=state_rslt
                        )

                    Session.add(instance_rslt)
                    Session.flush()

                    value.title = instance_rslt.title
                    setattr(value, '__id__', instance_rslt.id)

                for name, field_obj in zope.schema.getFieldsInOrder(schema_obj):
                    child = getattr(value, name, None)
                    to_visit.append((value, instance_rslt, name, child,))

            # Process an individual attribute
            else:

                attribute_rslt = Session.query(model.Attribute)\
                     .filter_by(name=unicode(attr_name))\
                     .join(model.Schema)\
                     .filter_by(id=parent_rslt.schema.id)\
                     .first()

                type_name = attribute_rslt.field.type.title

                if type_name not in name_model_map:
                    raise Exception('Type \'%s\' unsupported.' % type_name)

                Model = name_model_map[type_name]

                choice_values = dict()

                # We'll need a reverse dictionary of possible choices
                for choice_rslt in attribute_rslt.field.choices:
                    choice_values[choice_rslt.value] = choice_rslt

                value_query = Session.query(Model) \
                    .filter_by(instance=parent_rslt) \
                    .filter_by(attribute=attribute_rslt) \

                if attribute_rslt.field.is_list:
                    # Remove any existing values that are not in the new set
                    for value_rslt in value_query.all():
                        if value is None or value_rslt.value not in value:
                            Session.delete(value_rslt)

                    if value is not None:
                        for v in value:
                            if type_name in name_coalesce_map:
                                v = name_coalesce_map[type_name](v)

                            if attribute_rslt.field.is_list:
                                Session.add(Model(
                                    instance=parent_rslt,
                                    attribute=attribute_rslt,
                                    choice=choice_values.get(v),
                                    value=v
                                    ))
                else:
                    value_rslt = value_query.first()

                    if value is None:
                        if value_rslt is not None:
                            Session.delete(value_rslt)
                    else:
                        if value_rslt is None:
                            value_rslt = Model(
                                instance=parent_rslt,
                                attribute=attribute_rslt
                                )

                        if type_name in name_coalesce_map:
                            value = name_coalesce_map[type_name](value)

                        value_rslt.choice = choice_values.get(value)
                        value_rslt.value = value

                        if value_rslt.id is None:
                            Session.add(value_rslt)

            Session.flush()

        return target


    def purge(self, key):
        raise NotImplementedError()


    def retire(self, key):
        # we're going to use the object as the key (or it's 'name')
        Session = self.getScopedSession()

        if isinstance(key, basestring):
            key = str(key)
        elif interfaces.IInstance.providedBy(key):
            key = key.__id__
        else:
            raise Exception('The object specified cannot be evaluated into '
                            'a object to search for')

        instance_rslt = Session.query(model.Instance)\
            .filter_by(id=key)\
            .first()

        if instance_rslt:
            instance_rslt.is_active = False
            Session.flush()

        return instance_rslt is not None


    def restore(self, key):
        # we're going to use the object as the key (or it's 'name')
        Session = self.getScopedSession()

        if isinstance(key, basestring):
            key = str(key)
        elif interfaces.IInstance.providedBy(key):
            key = key.__id__
        else:
            raise Exception('The object specified cannot be evaluated into '
                            'a object to search for')

        instance_rslt = Session.query(model.Instance)\
            .filter_by(id=key)\
            .first()

        if instance_rslt:
            instance_rslt.is_active = True
            Session.flush()

        return instance_rslt is not None


    def spawn(self, target, **kw):
        if isinstance(target, basestring):
            iface = self.getSchemaManager().get(target)
        else:
            iface = target
        return spawnObject(iface, **kw)



DatastoreFactory = Factory(
    Datastore,
    title=_(u'Datastore implementation factory.'),
    description=_(u'Creates an instance of a datastore implementation object. '
                  u'Also notifies listeners of this creation.')
    )


def spawnObject(iface, **kw):
    """ Spawns 'anonymous' objects from interface specifications.

        Arguments:
            iface: (object) a zope Interface or child class
            **kw: (dict) additional arguments for the instantiated object
    """
    if not iface.extends(zope.interface.Interface):
        raise Exception('%s will not be found' % iface)

    class Instance(object):
        implements(interfaces.IInstance)

        __id__ = None
        __schema__ = None
        __state__ = None

        title = None
        description = None

        def setState(self, state):
            self.__state__ = unicode(state)

        def getState(self):
            return self.__state__

        # Note: DO NOT USE THIS, this is for backwards compatibility
        state = property(getState, setState)

        def __str__(self):
            return u'<Instance: \'%s\'; implements: \'%s\'>' \
                    % (self.title, self.__schema__.__name__)

    obj = Instance()
    directlyProvides(obj, iface)

    setattr(obj, '__schema__', iface)

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
    Session = datastore.getScopedSession()

    types = getUtility(zope.schema.interfaces.IVocabulary,
                       'avrc.data.store.Types')

    for t in list(types):
        num = Session.query(model.Type)\
            .filter_by(title=unicode(t.token))\
            .count()

        if not num:
            rslt.append(model.Type(
                title=unicode(t.token),
                description=unicode(getattr(t.value, '__doc__', None)),
                ))

    if rslt:
        Session.add_all(rslt)
        Session.flush()

def setup_states(datastore, state_vocabulary, default):
    """
    """
    Session = datastore.getScopedSession()

    states = []

    for term in list(state_vocabulary):
        name = unicode(term.token)
        title = term.title and unicode(term.title) or name
        is_default = name == default

        if Session.query(model.State).filter_by(name=name).count() < 1:
            states.append(model.State(name=name, title=title, is_default=is_default))

    if states:
        Session.add_all(states)
        Session.flush()
