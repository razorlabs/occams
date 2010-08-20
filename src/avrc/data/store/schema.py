"""
Responsible for schemata, attributes, and vocabularies

Additionally, we support plone.directives.form
"""
import itertools
from collections import deque as queue

from zope.component import adapter
from zope.component import adapts
from zope.component import getUtility
import zope.interface
from zope.interface import Interface
from zope.interface import implements
from zope.interface.interface import InterfaceClass
from zope.interface import directlyProvides
import zope.schema
from zope.schema.vocabulary import SimpleVocabulary
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

# The generated schemata of the datas tore will be contained here
virtual = dynamic.create(".".join([__name__, "virtual"]))

supported_directives_vocabulary = \
    SimpleVocabulary.fromValues([
        OMITTED_KEY,
        WIDGETS_KEY,
        MODES_KEY,
        ORDER_KEY,
        READ_PERMISSIONS_KEY,
        WRITE_PERMISSIONS_KEY
        ])

class SupportedDirectivesVocabularyFactory(object):
    implements(zope.schema.interfaces.IVocabularyFactory)

    def __call__(self, context=None):
        return supported_directives_vocabulary

def version(schema):
    """
    returns the version of the schema
    """
    return None

class Instance(object):
    """
    Empty object that will be used as the instance of a virtual schema.
    """

class DatastoreSchemaManager(object):
    """
    """
    adapts(interfaces.IDatastore)
    implements(interfaces.ISchemaManager)

    def __init__(self, datastore):
        self._datastore = datastore

    def get_descendants(self, ibase):
        """
        Retrieves the classes that inherit from the specified base.

        TODO: (mmartinez) support versioning?

        Arguments:
            base: (object) base interface to find all the children for
        Returns:
            list of interfaces that extend the specified base
        """
        Session = named_session(self._datastore)
        session  = Session()

        names = queue([])

        if not isinstance(ibase, (str, unicode)):
            if not ibase.extends(interfaces.Schema):
                raise Exception("base class does not extend datastore's base.")
            ibase_name = unicode(ibase.__name__)
        else:
            ibase_name = unicode(ibase)


        spec_rslt = session.query(model.Specification)\
                    .filter_by(name=ibase_name)\
                    .first()

        if spec_rslt is None:
            raise Exception("%s isn't in the data store" % ibase)

        to_visit = queue([spec_rslt])

        # Breadth-first pre-order traversal of all children
        while len(to_visit) > 0:
            spec_rslt = to_visit.popleft()

            if spec_rslt.children:
                for child in spec_rslt.children:
                    to_visit.append(child)

            names.append(spec_rslt.name)


        descendants = []

        # We don't want the root
        names.popleft()

        for name in names:
            descendants.append(self.get(name))

        return descendants

    def get_children(self, ibase):
        """
        Retrives all the children of the base class. Note this does not include
        all the intermediate bases (i.e. it just returns the leaf nodes)
        """
        Session = named_session(self._datastore)
        session  = Session()

        names = queue([])

        if not isinstance(ibase, (str, unicode)):
            if not ibase.extends(interfaces.Schema):
                raise Exception("base class does not extend datastore's base.")
            ibase_name = unicode(ibase.__name__)
        else:
            ibase_name = unicode(ibase)


        spec_rslt = session.query(model.Specification)\
                    .filter_by(name=ibase_name)\
                    .first()

        if spec_rslt is None:
            raise Exception("%s isn't in the data store" % ibase)

        to_visit = queue([spec_rslt])

        # Breadth-first pre-order traversal of all children
        while len(to_visit) > 0:
            spec_rslt = to_visit.popleft()

            if spec_rslt.children:
                for child in spec_rslt.children:
                    to_visit.append(child)
            else:
                # Only append if it's a leaf node (as opposed to descendants)
                names.append(spec_rslt.name)

        return [self.get(name) for name in names]

    def get(self, key):
        #
        # TODO: (mmartinez) Unable to retrieve versioned bases...
        # TODO: (mmartinez) Keep in mind that if getting many objects that
        #    share a common ancestor, this method might be inefficient unless
        #    dynamic programming heuristics are employed.
        #
        if isinstance(key, (str, unicode)):
            key  = (key, None)

        #key = module name, or (module name, version) tuple
        (name, version) = key
        name = unicode(name)

        types_factory = getUtility(zope.schema.interfaces.IVocabularyFactory,
                                   name="avrc.data.store.SupportedTypes")
        types = types_factory()

        Session = named_session(self._datastore)
        session = Session()

        schema_q = session.query(model.Schema)\
                      .join(model.Specification)\
                      .filter_by(name=name)

        if version is not None:
            schema_q = schema_q.filter_by(create_date=version)
        else:
            schema_q = schema_q.order_by(model.Schema.create_date.desc())

        schema_rslt = schema_q.first()

        bases = []
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

            field = types.getTermByToken(token).value

            kwargs = dict(
                title=attribute_rslt.field.title,
                description=attribute_rslt.field.description,
                required=attribute_rslt.field.is_required
                )

            if zope.schema.interfaces.IChoice.implementedBy(field):
                terms = []
                for term_rslt in attribute_rslt.field.vocabulary.terms:
                    terms.append(SimpleVocabulary.createTerm(
                        term_rslt.value,
                        str(term_rslt.token),
                        term_rslt.title,
                        ))

                kwargs["vocabulary"] = SimpleVocabulary(terms=terms)

            attrs[attribute_rslt.name] = field(**kwargs)

            name = str(attribute_rslt.name)

            if attribute_rslt.field.directive_omitted is not None:
                if attribute_rslt.field.directive_omitted:
                    value = "true"
                else:
                    value= "false"
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
            name=schema_rslt.specification.name,
            __doc__=schema_rslt.specification.documentation,
            __module__=virtual.__name__,
            bases=(interfaces.Schema,),
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
        num = session.query(model.Specification).filter_by(name=name).count()
        return num > 0

    def keys(self):
        """
        Returns a listing of the module names (with interface?)
        """
        Session = named_session(self._datastore)
        session = Session()
        keys = session.query(model.Specification.name).all()
        return list(itertools.chain.from_iterable(keys))

    def put(self, target):
        """
        Saves the target interface into the manager.
        """
        iface = target

        if not iface.extends(interfaces.Schema):
            raise Exception("%s must extend %s " % (iface, interfaces.Schema))

        types_factory = getUtility(zope.schema.interfaces.IVocabularyFactory,
                                   name="avrc.data.store.SupportedTypes")
        types = types_factory()

        Session = named_session(self._datastore)
        session = Session()

        spec_rslt = session.query(model.Specification)\
                    .filter_by(name=iface.__name__)\
                    .first()

        # Create a spec if one doesn't already exist
        if spec_rslt is None:
            spec_rslt = model.Specification(
                name=unicode(iface.__name__),
                documentation=(iface.__doc__)
                )


            for ibase in iface.__bases__:
                # only associate with interfaces that are also marked as part
                # of the data store schemata
                if ibase.extends(interfaces.Schema):
                    base_rslt = session.query(model.Specification)\
                                .filter_by(name=unicode(ibase.__name__))\
                                .first()

                    if base_rslt is None:
                        raise Exception("%s extends a base (%s) interface that is "
                                        "not in the datastore" % (iface, ibase))

                    spec_rslt.bases.append(base_rslt)

        schema_rslt = model.Schema(specification=spec_rslt)

        attrs = {}

        # Now add/remove in all the changed fields
        for name, field_obj in zope.schema.getFieldsInOrder(iface):
            type_obj = field_obj
            is_repeatable = False

            if isinstance(field_obj, zope.schema.List):
                type_obj = field_obj.value_type
                is_repeatable = True

            if type_obj.__class__ not in types:
                session.rollback()
                raise Exception("Not supported: %s" % str(type_obj.__class__))

            term_obj = types.getTerm(type_obj.__class__)

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
                    is_required=is_repeatable,
                    )
                )

            if zope.schema.interfaces.IChoice.providedBy(field_obj):
                vocabulary_obj = field_obj.vocabulary
                # TODO: need a better name for this
                vocabulary_rslt = model.Vocabulary(title="blablah")

                for i, term_obj in enumerate(vocabulary_obj, start=1):
                    term_rslt = model.Term(
                        title=term_obj and unicode(term_obj.title) or None,
                        token=unicode(term_obj.token),
                        order=i
                        )

                    term_rslt.value = term_obj.value

                    vocabulary_rslt.terms.append(term_rslt)

                attrs[name].field.vocabulary = vocabulary_rslt

            if zope.schema.interfaces.IObject.providedBy(field_obj):
                # TODO link to versioned schema_obj.
                raise NotImplementedError("Don't supported nested objects yet")

            schema_rslt.attributes.append(attrs[name])

        tags = iface.queryTaggedValue(TEMP_KEY, {})

        if tags:
            for key, item in tags.items():
                if key not in supported_directives_vocabulary:
                    continue

                try:
                    if key is OMITTED_KEY:
                        for interface, name, value in item:
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

        iface.__version__ = schema_rslt.create_date
        return iface

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

    def spawn(self, target, **kw):
        """
        Generates an object that implements this schema
        """

        if isinstance(target, str):
            iface = self.get(target)
        else:
            iface = target

        if not iface.extends(interfaces.Schema):
            raise Exception("This will not be found")

        obj = Instance()
        directlyProvides(obj, iface)

        for name in zope.schema.getFieldNamesInOrder(iface):
            setattr(obj, name, FieldProperty(iface[name]))
            obj.__dict__[name].__set__(obj, kw.get(name))

        return obj
