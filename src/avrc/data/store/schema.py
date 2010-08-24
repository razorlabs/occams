"""
Responsible for schemata, attributes, and vocabularies

Additionally, we support plone.directives.form
"""
import itertools
from collections import deque as queue

from zope.component import adapts
from zope.component import getUtility
from zope.interface import Interface
from zope.interface import implements
from zope.interface.interface import InterfaceClass
import zope.schema
from zope.schema.interfaces import IVocabulary
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.vocabulary import SimpleTerm
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
from avrc.data.store.datastore import Instance

_ = MessageFactory(__name__)

#
# The generated schemata of the data store will be contained here
#
virtual = dynamic.create("avrc.data.store.schema.virtual")

#
# Helper vocabulary for directives
#
supported_directives_vocabulary = SimpleVocabulary.fromValues([
    OMITTED_KEY,
    WIDGETS_KEY,
    MODES_KEY,
    ORDER_KEY,
    READ_PERMISSIONS_KEY,
    WRITE_PERMISSIONS_KEY
    ])

def version(iface):
    """
    Helper method to get the interface's version.

    Arguments:
        iface: (class) an interface class that must extend the Schema marker
            interface
    Returns:
        interface version object
    Raises:
        Exception
    """
    if iface.extends(interfaces.Schema):
        return iface.__version__
    else:
        raise Exception("%s doesn't extend %s", (iface, interfaces.Schema))

class DependencyGenerator(object):
    """
    The purpose of this class is to attempt to 'lighten' the load of using
    interfaces throughout the client application, since dependent interfaces
    will only be used when generating forms and not checking objects.
    """

    def __init__(self, manager, imain, names):
        """
        Arguments:
            imain: the interface this generator is contained in
            manager: the manager that is using this generator
            names: the names of the dependent interfaces
        """
        self.imain = imain
        self.manager = manager
        self.names = names

    def __iter__(self):
        """
        TODO: can't handle versioning yet
        """
        for name in self.names:
            yield self.manager.get(name)

class DatastoreSchemaManager(object):
    adapts(interfaces.IDatastore)
    implements(interfaces.ISchemaManager)

    __doc__ = interfaces.ISchemaManager.__doc__

    def __init__(self, datastore):
        self._datastore = datastore

    def get_descendants(self, ibase):
        #
        #  TODO: (mmartinez) support versioning?
        #
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

    get_descendants.__doc__ = \
        interfaces.ISchemaManager["get_descendants"].__doc__

    def get_children(self, ibase):
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

    get_children.__doc__ = interfaces.ISchemaManager["get_children"].__doc__

    def get(self, key):
        #
        # TODO: (mmartinez) Unable to retrieve versioned bases (sort of, it
        #    currently retieves the highest version up to the version of
        #     the retrieved interface
        # TODO: (mmartinez) Keep in mind that if getting many objects that
        #    share a common ancestor, this method might be inefficient unless
        #    dynamic programming heuristics are employed.
        #
        if isinstance(key, (str, unicode)):
            key = (key, None)

        (name, version) = key
        name = unicode(name)

        types = getUtility(IVocabulary, "avrc.data.store.Types")

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

        if schema_rslt is None:
            raise Exception("Schema Manager doesn't have %s" % name)

        visited = {}

        to_visit = [schema_rslt]

        # accomplished via depth-first post-order traversal (iterative)
        while to_visit:
            schema_rslt= to_visit[-1]
            children_visited = True

            for ibase_rslt in schema_rslt.specification.bases:
                if not ibase_rslt.name in visited:
                    base_q = session.query(model.Schema)\
                                .filter_by(specification=ibase_rslt)

                    if version:
                        base_q = base_q.filter(model.Schema.create_date <= version)

                    base_q = base_q.order_by(model.Schema.create_date.desc())
                    base_rslt = base_q.first()

                    children_visited = False
                    to_visit.append(base_rslt)

            if not children_visited:
                continue

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
                        terms.append(SimpleTerm(
                            value=term_rslt.value,
                            token=str(term_rslt.token),
                            title=term_rslt.title,
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

            bases = [visited[ibase_rslt.name] for ibase_rslt in schema_rslt.specification.bases]

            if not bases:
                bases = [interfaces.Schema]

            iface = InterfaceClass(
                name=schema_rslt.specification.name,
                __doc__=schema_rslt.specification.documentation,
                __module__=virtual.__name__,
                bases=bases,
                attrs=attrs,
                )

            setattr(virtual, iface.__name__, iface)
            setattr(iface, "__title__", schema_rslt.specification.title)
            setattr(iface, "__description__", schema_rslt.specification.description)
            setattr(iface, "__version__", schema_rslt.create_date)
            setattr(iface, "__dependents__", DependencyGenerator(self, iface, [s.name for s in schema_rslt.specification.includes]))

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

            visited[schema_rslt.specification.name] = iface
            to_visit.pop()

        return iface

    get.__doc__ = interfaces.ISchemaManager["get"].__doc__

    def has(self, key):
        Session = named_session(self._datastore)
        session = Session()
        name = unicode(key)
        num = session.query(model.Specification).filter_by(name=name).count()
        return num > 0

    has.__doc__ = interfaces.ISchemaManager["has"].__doc__

    def keys(self):
        Session = named_session(self._datastore)
        session = Session()
        keys = session.query(model.Specification.name).all()
        return list(itertools.chain.from_iterable(keys))

    keys.__doc__ = interfaces.ISchemaManager["keys"].__doc__

    def put(self, target):
        iface = target

        if not iface.extends(interfaces.Schema):
            raise Exception("%s must extend %s " % (iface, interfaces.Schema))

        types = getUtility(IVocabulary, "avrc.data.store.Types")
        directives = getUtility(IVocabulary, "avrc.data.store.Directives")

        Session = named_session(self._datastore)
        session = Session()

        spec_rslt = session.query(model.Specification)\
                    .filter_by(name=unicode(iface.__name__))\
                    .first()

        # Create a spec if one doesn't already exist
        if spec_rslt is None:
            spec_rslt = model.Specification(
                name=unicode(iface.__name__),
                documentation=unicode(iface.__doc__),
                title=unicode(getattr(iface, "__title__", None)),
                description=unicode(getattr(iface, "__description__", None))
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

        for idependent in getattr(iface, "__dependents__", []):
            #
            # TODO: versioning
            #
            dependent_rslt = session.query(model.Specification)\
                          .filter_by(name=unicode(idependent.__name__))\
                          .first()

            schema_rslt.specification.includes.append(dependent_rslt)

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
                raise Exception("%s defines a field that is not supported: %s" % (iface, type_obj.__class__))

            term_obj = types.getTerm(type_obj.__class__)

            type_rslt = session.query(model.Type)\
                        .filter_by(title=unicode(term_obj.token))\
                        .first()

            attrs[name] = model.Attribute(
                name=unicode(name),
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
                vocabulary_rslt = model.Vocabulary(title=u"")

                for i, term_obj in enumerate(vocabulary_obj, start=1):

                    term_rslt = model.Term(
                        title=term_obj.title and unicode(term_obj.title) or None,
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

        tags = iface.queryTaggedValue(TEMP_KEY, {}) or {}

        for key, item in tags.items():
            if key in directives:
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
                                raise Exception("order %s is not supported" % order)
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

    put.__doc__ = interfaces.ISchemaManager["put"].__doc__

    def purge(self, key):
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

    purge.__doc__ = interfaces.ISchemaManager["purge"].__doc__

    def retire(self, key):
        # Will fail, schema managers cannot be "retired".
        # TODO: why?
        raise Exception("Can't retire schemata")

    retire.__doc__ = interfaces.ISchemaManager["retire"].__doc__
