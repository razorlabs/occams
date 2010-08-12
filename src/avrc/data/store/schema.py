"""
Responsible for schemata, attributes, and vocabularies

Additionally, we support plone.directives.form
"""
import itertools

from zope.component import adapter
from zope.component import adapts
from zope.component import getUtility
import zope.interface
from zope.interface import implements
from zope.interface.interface import InterfaceClass
from zope.interface import Interface
from zope.interface import alsoProvides
import zope.schema
from zope.schema.fieldproperty import FieldProperty
from zope.i18nmessageid import MessageFactory

from plone.alterego import dynamic

# Placing all directives under dexterity's namespace
from plone.directives.form.schema import TEMP_KEY

# Necessary keys for directives
from plone.autoform.interfaces import OMITTED_KEY
from plone.autoform.interfaces import WIDGETS_KEY
from plone.autoform.interfaces import MODES_KEY
from plone.autoform.interfaces import ORDER_KEY
from plone.autoform.interfaces import READ_PERMISSIONS_KEY
from plone.autoform.interfaces import WRITE_PERMISSIONS_KEY

from avrc.data.store import interfaces
from avrc.data.store import model
from avrc.data.store.datastore import named_session

_ = MessageFactory(__name__)

# Stored schemata will be summoned from the nether with a virtual name space
virtual = dynamic.create(".".join([__name__, "virtual"]))

supported_types_vocabulary = \
    zope.schema.vocabulary.SimpleVocabulary.fromItems([
        ("integer", zope.schema.Int),
        ("string", zope.schema.TextLine),
        ("text", zope.schema.Text),
        ("binary", zope.schema.Bytes),
        ("boolean", zope.schema.Bool),
        ("real", zope.schema.Decimal),
        ("date", zope.schema.Date),
        ("datetime", zope.schema.Datetime),
        ("time", zope.schema.Time),
        ("object", zope.schema.Object),
        ])

supported_directives_vocabulary = \
    zope.schema.vocabulary.SimpleVocabulary.fromValues([
        OMITTED_KEY,
        WIDGETS_KEY,
        MODES_KEY,
        ORDER_KEY,
        READ_PERMISSIONS_KEY,
        WRITE_PERMISSIONS_KEY
        ])

def SupportedTypesVocabularyFactory(context=None):
    """
    Convenience factory for getting the supported types vocabulary
    This is used for auto-generating meta data into the data store once it
    is added into a site.
    """
    return supported_types_vocabulary

alsoProvides(SupportedTypesVocabularyFactory,
             zope.schema.interfaces.IVocabularyFactory)

def SupportedDirectivesVocabularyFactory(context=None):
    """
    Convenience method for getting the supported directives.
    """
    return supported_directives_vocabulary

alsoProvides(SupportedDirectivesVocabularyFactory,
             zope.schema.interfaces.IVocabularyFactory)

def version(schema):
    """
    returns the version of the schema
    """
    return None

@adapter(interfaces.IMutableSchema)
#@provides(zope.interface.interfaces.IInterface)
def MutableSchemaInterface(ms):
    """
    Possibly somehow convert a mutable schema to zope interface
    """

class VocabularyManager(object):
    """
    """
    implements(interfaces.ISchemaManager)

    def __init__(self):
        """
        """

    def put(self, source):
        """
        """
        for term in source:
            pass

class VocabularySchema(object):
    """
    I don't know what this does yet, just skeching
    """
    adapts(zope.schema.interfaces.IVocabulary)
    implements(interfaces.ISchemaManager)

    def __int__(self, vocabulary):
        """
        """

class Instance(object):
    """
    """
    pass


class DatastoreSchemaManager(object):
    """
    """
    adapts(interfaces.IDatastore)
    implements(interfaces.ISchemaManager)

    def __init__(self, datastore):
        self._datastore = datastore

    def get(self, key):
        """
        key = module name, or (module name, version) tuple
        """
        if isinstance(key, str):
            key  = (key, None)

        (name, version) = key
        name = unicode(name)

        Session = named_session(self._datastore)
        session = Session()

        schema_q = session.query(model.Schema)\
                      .join(model.Specification)\
                      .filter_by(module=name)

        if version is not None:
            schema_q = schema_q.filter_by(create_date=version)
        else:
            schema_q = schema_q.order_by(model.Schema.create_date.desc())

        schema_rslt = schema_q.first()

        attrs = {}
        directives = {}
        omitted = []
        widgets = {}
        modes = []
        order = []
        read = {}
        write = {}

        for attribute_rslt in schema_rslt.attributes:
            token = str(attribute_rslt.field.type.title)
            field = supported_types_vocabulary.getTermByToken(token).value
            attrs[attribute_rslt.name] = field(
                title=attribute_rslt.field.title,
                description=attribute_rslt.field.description,
                required=attribute_rslt.field.is_required
                )

            name = str(attribute_rslt.name)

            if attribute_rslt.field.directive_omitted is not None:
                value = attribute_rslt.field.directive_omitted and "true" or "false"
                omitted.append(tuple([Interface, name, value]))
            elif attribute_rslt.field.directive_widget is not None:
                widgets[name] = str(attribute_rslt.field.directive_widget)
            if attribute_rslt.field.directive_mode is not None:
                value = str(attribute_rslt.field.directive_mode)
                modes.append(tuple([Interface, name, value]))
            if attribute_rslt.field.directive_before is not None:
                value = str(attribute_rslt.field.directive_before)
                order.append(tuple([name, "before", value]))
            if attribute_rslt.field.directive_after is not None:
                value = str(attribute_rslt.field.directive_after)
                order.append(tuple([name, "after", value]))
            elif attribute_rslt.field.directive_read is not None:
                read[name] = str(attribute_rslt.field.directive_read)
            elif attribute_rslt.field.directive_write is not None:
                write[name] = str(attribute_rslt.field.directive_write)

        iface = InterfaceClass(
            name=schema_rslt.specification.module,
            __doc__=schema_rslt.specification.documentation,
            __module__=virtual.__name__,
            bases=tuple([interfaces.ISchema]),
            attrs=attrs,
            )

        setattr(iface, "__version__", schema_rslt.create_date)

        if len(omitted) > 0:
            directives[OMITTED_KEY] = omitted
        if len(widgets) > 0:
            directives[WIDGETS_KEY] = widgets
        if len(modes) > 0:
            directives[MODES_KEY] = modes
        if len(order) > 0:
            directives[ORDER_KEY] = order
        if len(read) > 0:
            directives[READ_PERMISSIONS_KEY] = read
        if len(write) > 0:
            directives[WRITE_PERMISSIONS_KEY] = write

        if len(directives) > 0:
            iface.setTaggedValue(TEMP_KEY, directives)

        return iface

    def has(self, key):
        """
        Checks if the module name (key) exists
        """
        Session = named_session(self._datastore)
        session = Session()
        name = unicode(key)
        num = session.query(model.Specification).filter_by(module=name).count()
        return num > 0

    def keys(self):
        """
        Returns a listing of the module names (with interface?)
        """
        Session = named_session(self._datastore)
        session = Session()
        keys = session.query(model.Specification.module).all()
        return list(itertools.chain.from_iterable(keys))

    def put(self, target):
        """
        Saves the target interface into the manager.
        """
        schema = target
        Session = named_session(self._datastore)
        session = Session()

        spec_rslt = session.query(model.Specification)\
                    .filter_by(module=schema.__module__)\
                    .first()

        # Create a spec if one doesn't already exist
        if spec_rslt is None:
            spec_rslt = model.Specification(
                module=schema.__module__,
                documentation=schema.__documentation__
                )

        schema_rslt = model.Schema(specification=spec_rslt)

        # Need toe old schema (if any) to copy over unchanged fields
        schema_old_rslt = session.query(model.Schema)\
                          .filter_by(create_date=schema.__version__)\
                          .join(model.Specification)\
                          .filter_by(module=schema.__module__)\
                          .first()

        if schema_old_rslt is not None:
            for attribute_rslt in schema_old_rslt.attributes:
                # Copy unchanged properties from the last version
                if attribute_rslt.name not in schema.__attributes__:
                    schema_rslt.attributes.append(model.Attribute(
                        name=attribute_rslt.name,
                        order=attribute_rslt.order,
                        field=attribute_rslt.field
                        ))

            for invariant_rslt in schema_old_rslt.invariants:
                if invariant_rslt.name not in schema.__invariants__:
                    schema_rslt.invariants.append(model.Invariant(
                        name=invariant_rslt.name
                        ))

        attrs = {}

        # Now add/remove in all the changed fields
        for name, field_obj in schema.__attributes__.items():
            if field_obj.__class__ not in supported_types_vocabulary:
                continue
                session.rollback()
                raise Exception("Not supported: %s" % str(field_obj.__class__))

            term_obj = supported_types_vocabulary.getTerm(field_obj.__class__)

            type_rslt = session.query(model.Type)\
                        .filter_by(title=unicode(term_obj.token))\
                        .first()

            attrs[name] = model.Attribute(
                name=name,
                order=field_obj.order,
                field=model.Field(
                    title=unicode(field_obj.title),
                    description=unicode(field_obj.description),
                    type=type_rslt,
                    is_required=field_obj.required,
                    )
                )

            if hasattr(field_obj, "schema"):
                # TODO link to versioned schema. said schema must extend
                # IVersionedSchema?
                pass


            schema_rslt.attributes.append(attrs[name])

        for key, item in schema.__directives__.items():
            if key not in supported_directives_vocabulary:
                continue

            try:
                if key is OMITTED_KEY:
                    for interface, name, value in item:
                        # Interface is ignored since it's just going to the base
                        attrs[name].field.directive_omitted = value is "true"
                elif key is WIDGETS_KEY:
                    for name, module in item.items():
                        attrs[name].field.directive_widget = unicode(module)
                elif key is MODES_KEY:
                    for interface, name, value in item:
                        attrs[name].field.directive_mode = unicode(value)
                elif key is ORDER_KEY:
                    for name, order, target in item:
                        if order is "before":
                            attrs[name].field.directive_before = value
                        elif order is "after":
                            attrs[name].field.directive_after = value
                        else:
                            raise Exception("WTF")
                elif key is READ_PERMISSIONS_KEY:
                    for name, value in item.items():
                        attrs[name].field.directive_read = unicode(value)
                elif key is WRITE_PERMISSIONS_KEY:
                    for name, value in item.items():
                        attrs[name].field.directive_write = unicode(value)
            except KeyError:
                continue


        session.add(schema_rslt)
        session.commit()
        schema.__attributes__ = {}
        schema.__invariants__.clear()

    def purge(self, key):
        """
        Removes the interface from the manager (completely)
        """
        Session = named_session(self._datastore)
        session = Session()

        num_instances = session.query(model.Instance)\
                        .join(model.Schema.specification)\
                        .filter_by(module=self._module)\
                        .count()

        if num_instances > 0:
            raise Exception("There is already data stored for %s" % self._module)

        schema_rslt = session.query(model.Schema)\
                      .join(model.Specification)\
                      .filter_by(module=self._module)\
                      .first()

        session.remove(schema_rslt)
        session.commit()

    def retire(self, key):
        """
        Will fail, schema managers cannot be "retired".
        TODO: why?
        """
        raise Exception("Can't retire schemata")


    def import_(self, iface):
        """
        Imports the target interface into the manager.
        """
        schema_obj = MutableSchema(module=unicode(iface.__name__),
                         documentation=unicode(iface.__doc__),
                         directives=iface.queryTaggedValue(TEMP_KEY)
                         )

        for name, field in zope.schema.getFieldsInOrder(iface):
            schema_obj[unicode(name)] = field

        self.put(schema_obj)

    def spawn(self, target, **kw):
        """
        Generates an object that implements this schema
        """

        if isinstance(target, str):
            iface = self.get(target)
        else:
            iface = target

        if not iface.extends(interfaces.ISchema):
            raise Exception("This will not be found")

        obj = Instance()
        alsoProvides(obj, iface)

        for name in zope.schema.getFieldNamesInOrder(iface):
            setattr(obj, name, FieldProperty(iface[name]))
            obj.__dict__[name].__set__(obj, kw.get(name))

        return obj


class MutableSchema(object):
    """
    This module is in charge of controlling the actual properties of the
    target module. It's sole purpose is for writing, not retrieving properties.

    Behaves like a delta of the last version and this version.
    """

    implements(interfaces.IMutableSchema)

    __version__ = None

    __module__ = None

    __documentation__ = None

    __attributes__ = None

    __directives__ = None

    __invariants__ = None

    def __init__(self,
                 module,
                 documentation=None,
                 directives=None,
                 version=None):
        """
        Constructor
        """
        self.__module__ = unicode(module)
        self.__documentation__ = unicode(documentation)
        self.__version__ = version
        self.__attributes__ = {}
        self.__directives__ = directives or {}
        self.__invariants__ = set([])

    def add_invariant(self, name):
        """
        """
        self.__invariants__.add(unicode(name))

    def remove_invariant(self, name):
        """
        """
        try:
            self.__invariants__.remove(unicode(name))
        except KeyError:
            pass

    def __setitem__(self, name, field_obj):
        """
        @param key: the name of the property to change
        @param value: the zope schema value to set for the property, None to
                      remove the property
        """
        if isinstance(field_obj, zope.schema.Object):
            exists = MutableSchema.has_interface(field_obj.schema.__name__,
                                                 version=None)
            if not exists:
                raise interfaces.UndefinedSchemaError()

        self.__attributes__[unicode(name)] = field_obj
