""" Responsible for schemata, attributes, and vocabularies
    Additionally, we support plone.directives.form
"""
import itertools
from collections import deque as queue

from zope.component import adapts
from zope.component import getUtility
from zope.interface import Interface
from zope.interface import implements
from zope.interface import classProvides
from zope.interface.interface import InterfaceClass
import zope.schema
from zope.schema.interfaces import IVocabulary
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.vocabulary import SimpleTerm

from plone.alterego import dynamic

# Necessary keys for directives
from plone.autoform.interfaces import OMITTED_KEY
from plone.autoform.interfaces import WIDGETS_KEY
from plone.autoform.interfaces import MODES_KEY
from plone.autoform.interfaces import ORDER_KEY
from plone.autoform.interfaces import READ_PERMISSIONS_KEY
from plone.autoform.interfaces import WRITE_PERMISSIONS_KEY

from plone.supermodel.interfaces import FIELDSETS_KEY
from plone.supermodel.model import Fieldset

from avrc.data.store._manager import AbstractDatastoreManager
from avrc.data.store.interfaces import IDatastore
from avrc.data.store.interfaces import IManagerFactory
from avrc.data.store.interfaces import ISchemaManager
from avrc.data.store.interfaces import Schema
from avrc.data.store import model


#
# The generated schemata of the data store will be contained here
# TODO: (mmartinez) it would probably be a good idea to integrate with
#    alter-ego fully and create the interface factory so we stop getting
#    different (but same, technically) interface objects
#
virtual = dynamic.create('avrc.data.store.schema.virtual')

#
# Helper vocabulary for directives
#
supported_directives_vocabulary = SimpleVocabulary.fromValues([
    OMITTED_KEY,
    WIDGETS_KEY,
    MODES_KEY,
    ORDER_KEY,
    READ_PERMISSIONS_KEY,
    WRITE_PERMISSIONS_KEY,
    FIELDSETS_KEY
    ])


#
# Supported types
#
supported_types_vocabulary = SimpleVocabulary.fromItems([
    ('integer', zope.schema.Int),
    ('string', zope.schema.TextLine),
    ('text', zope.schema.Text),
    ('boolean', zope.schema.Bool),
    ('real', zope.schema.Float),
    ('date', zope.schema.Date),
    ('datetime', zope.schema.Datetime),
    ('time', zope.schema.Time),
    ])

python_zope_map = {
    int: zope.schema.Int,
    str: zope.schema.TextLine,
    unicode: zope.schema.TextLine,
    bool: zope.schema.Bool,
    float: zope.schema.Float,
    }

def version(iface):
    """ Helper method to get the interface's version.

        Arguments:
            iface: (class) an interface class that must extend the Schema marker
                interface
        Returns:
            interface version object
        Raises:
            Exception
    """
    if iface.extends(Schema):
        return iface.__version__
    else:
        raise Exception('%s doesn\'t extend %s', (iface, Schema))


class DependencyGenerator(object):
    """ The purpose of this class is to attempt to 'lighten' the load of using
        interfaces throughout the client application, since dependent interfaces
        will only be used when generating forms and not checking objects.
    """

    def __init__(self, manager, imain, names):
        """ Arguments:
                imain: the interface this generator is contained in
                manager: the manager that is using this generator
                names: the names of the dependent interfaces
        """
        self.imain = imain
        self.manager = manager
        self.names = names


    def __iter__(self):
        """ TODO: can't handle versioning yet """
        for name in self.names:
            yield self.manager.get(name)

class DatastoreSchemaManager(AbstractDatastoreManager):
    implements(ISchemaManager)
    classProvides(IManagerFactory)
    adapts(IDatastore)


    def get_descendants(self, ibase):
        #
        #  TODO: (mmartinez) support versioning?
        #
        Session = self._datastore.getScopedSession()

        names = queue([])

        if not isinstance(ibase, basestring):
            if not ibase.extends(Schema):
                raise Exception('base class does not extend datastore\'s base.')
            ibase_name = unicode(ibase.__name__)
        else:
            ibase_name = unicode(ibase)


        spec_rslt = Session.query(model.Specification)\
                    .filter_by(name=ibase_name)\
                    .first()

        if spec_rslt is None:
            raise Exception('%s isn\'t in the data store' % ibase)

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
        Session = self._datastore.getScopedSession()

        names = queue([])

        if not isinstance(ibase, basestring):
            if not ibase.extends(Schema):
                raise Exception('base class does not extend datastore\'s base.')
            ibase_name = unicode(ibase.__name__)
        else:
            ibase_name = unicode(ibase)

        spec_rslt = Session.query(model.Specification)\
                    .filter_by(name=ibase_name)\
                    .first()

        if spec_rslt is None:
            raise Exception('%s isn\'t in the data store' % ibase)

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
        # TODO: (mmartinez) Unable to retrieve versioned bases (sort of, it
        #    currently retieves the highest version up to the version of
        #     the retrieved interface
        # TODO: (mmartinez) Keep in mind that if getting many objects that
        #    share a common ancestor, this method might be inefficient unless
        #    dynamic programming heuristics are employed.
        #
        if isinstance(key, basestring):
            key = (key, None,)

        Session = self._datastore.getScopedSession()

        (name, version) = key

        types = supported_types_vocabulary

        schema_query = Session.query(model.Schema)\
          .join(model.Specification)\
          .filter_by(name=name)

        if version is not None:
            schema_query = schema_query\
                .filter(model.Schema.create_date == version)
        else:
            schema_query = schema_query\
                .order_by(model.Schema.create_date.desc())

        schema_rslt = schema_query.first()

        if schema_rslt is None:
            raise Exception('Schema Manager doesn\'t have %s' % name)

        visited = dict()

        to_visit = [schema_rslt]

        # Accomplished via depth-first post-order traversal (iterative)
        while to_visit:
            schema_rslt = to_visit[-1]
            children_visited = True

            # Process the base classes first
            for ibase_rslt in schema_rslt.specification.bases:
                if not ibase_rslt.name in visited:
                    base_q = Session.query(model.Schema)\
                        .filter_by(specification=ibase_rslt)

                    if version:
                        base_q = base_q\
                            .filter(model.Schema.create_date <= version)

                    base_q = base_q.order_by(model.Schema.create_date.desc())
                    base_rslt = base_q.first()

                    children_visited = False
                    to_visit.append(base_rslt)

            if not children_visited:
                continue

            bases = []
            attrs = dict()
            directives = dict()
            omitted = []
            widgets = dict()
            modes = []
            order = []
            read = dict()
            write = dict()

            # Build the zope schema fields
            for attribute_rslt in schema_rslt.attributes:

                if attribute_rslt.name == u'state':
                    continue

                type_name = str(attribute_rslt.field.type.title)

                # Process the field as the given EAV type
                FieldType = types.getTermByToken(type_name).value

                vocabulary = None

                kwargs = dict(
                    title=attribute_rslt.field.title,
                    description=attribute_rslt.field.description,
                    required=attribute_rslt.field.is_required,
                    readonly=attribute_rslt.field.is_readonly,
                    )

                if attribute_rslt.field.default is not None:
                    if hasattr(FieldType, 'fromUnicode'):
                        default_raw = attribute_rslt.field.default
                        default = FieldType().fromUnicode(default_raw)
                    else:
                        message = '%s default values  not implemented'
                        raise NotImplementedError(message % type_name)

                    kwargs['default'] = default

                if attribute_rslt.field.choices:
                    terms = []

                    for choice_rslt in attribute_rslt.field.choices:
                        if hasattr(FieldType, 'fromUnicode'):
                            value_raw = choice_rslt.value
                            value = FieldType().fromUnicode(value_raw)
                        else:
                            message = '%s choice values  not implemented'
                            raise NotImplementedError(message % type_name)

                        terms.append(SimpleTerm(
                            token=str(choice_rslt.name),
                            title=choice_rslt.title,
                            value=value,
                            ))

                    vocabulary = SimpleVocabulary(terms=terms)

                name = str(attribute_rslt.name)

                # Now assign the field as something Zope understands
                if attribute_rslt.field.choices:
                    Field = zope.schema.Choice
                else:
                    Field = FieldType

                if attribute_rslt.field.is_list:
                    subkw = {}
                    if vocabulary:
                        subkw['vocabulary'] = vocabulary
                    kwargs['value_type'] = Field(**subkw)
                    attrs[name] = zope.schema.List(**kwargs)
                else:
                    if vocabulary:
                        kwargs['vocabulary'] = vocabulary
                    attrs[name] = Field(**kwargs)

                # Process Plone directives
                if attribute_rslt.field.directive_omitted is not None:
                    if attribute_rslt.field.directive_omitted:
                        value = 'true'
                    else:
                        value = 'false'
                    omitted.append(tuple([Interface, name, value]))
                elif attribute_rslt.field.directive_widget is not None:
                    widgets[name] = str(attribute_rslt.field.directive_widget)
                if attribute_rslt.field.directive_mode is not None:
                    value = str(attribute_rslt.field.directive_mode)
                    modes.append(tuple([Interface, name, value]))
                if attribute_rslt.field.directive_before is not None:
                    value = str(attribute_rslt.field.directive_before)
                    order.append(tuple([name, 'before', value]))
                if attribute_rslt.field.directive_after is not None:
                    value = str(attribute_rslt.field.directive_after)
                    order.append(tuple([name, 'after', value]))
                elif attribute_rslt.field.directive_read is not None:
                    read[name] = str(attribute_rslt.field.directive_read)
                elif attribute_rslt.field.directive_write is not None:
                    write[name] = str(attribute_rslt.field.directive_write)

            bases = [visited[b.name] for b in schema_rslt.specification.bases]

            if not bases:
                bases = [Schema]

            iface = InterfaceClass(
                name=str(schema_rslt.specification.name),
                __doc__=schema_rslt.specification.documentation,
                __module__=virtual.__name__,
                bases=bases,
                attrs=attrs,
                )

            setattr(virtual, iface.__name__, iface)
            setattr(iface, '__version__', schema_rslt.create_date)
            setattr(iface, '__title__', schema_rslt.specification.title)
            description = schema_rslt.specification.description
            setattr(iface, '__description__', description)
            include_names = [s.name for s in schema_rslt.specification.includes]
            generator = DependencyGenerator(self, iface, include_names)
            setattr(iface, '__dependents__', generator)
            setattr(iface, '__is_tabable__', False)

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

            for fieldset_rslt in schema_rslt.fieldsets:
                if FIELDSETS_KEY not in directives:
                    directives[FIELDSETS_KEY] = []

                directives[FIELDSETS_KEY].append(Fieldset(
                    __name__=str(fieldset_rslt.name),
                    label=fieldset_rslt.label,
                    description=fieldset_rslt.description,
                    fields=[str(f.name) for f in fieldset_rslt.fields]
                    ))

            for key, item in directives.items():
                iface.setTaggedValue(key, item)

            visited[schema_rslt.specification.name] = iface
            to_visit.pop()

        return iface


    def get_children_names(self, ibase):
        Session = self._datastore.getScopedSession()

        names = queue([])

        if not isinstance(ibase, basestring):
            if not ibase.extends(Schema):
                raise Exception('base class does not extend datastore\'s base.')
            ibase_name = unicode(ibase.__name__)
        else:
            ibase_name = unicode(ibase)

        spec_rslt = Session.query(model.Specification)\
                    .filter_by(name=ibase_name)\
                    .first()

        if spec_rslt is None:
            raise Exception('%s isn\'t in the data store' % ibase)

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

        return [self.get_child_name_term(name) for name in names]


    def get_child_name_term(self, key):
        # NOTE: (dmote) We only need a small chunk of the schema when producing
        # a list of the schema

        if isinstance(key, basestring):
            key = (key, None)

        (name, version) = key
        name = unicode(name)

        Session = self._datastore.getScopedSession()

        schema_q = Session.query(model.Schema)\
                      .join(model.Specification)\
                      .filter_by(name=name)

        if version is not None:
            schema_q = schema_q.filter_by(create_date=version)
        else:
            schema_q = schema_q.order_by(model.Schema.create_date.desc())

        schema_rslt = schema_q.first()

        if schema_rslt is None:
            raise Exception('Schema Manager doesn\'t have %s' % name)

        return SimpleTerm(
            title=schema_rslt.specification.title,
            token=str(schema_rslt.specification.name),
            value=schema_rslt.specification.name)


    def has(self, key):
        Session = self._datastore.getScopedSession()
        name = unicode(key)
        num = Session.query(model.Specification).filter_by(name=name).count()
        return num > 0


    def keys(self):
        Session = self._datastore.getScopedSession()
        keys = Session.query(model.Specification.name).all()
        return list(itertools.chain.from_iterable(keys))


    def put(self, target):
        iface = target

        if not iface.extends(Schema):
            raise Exception('%s must extend %s ' % (iface, Schema))

        types = supported_types_vocabulary
        directives = supported_directives_vocabulary

        Session = self._datastore.getScopedSession()

        spec_rslt = Session.query(model.Specification)\
            .filter_by(name=unicode(iface.__name__))\
            .first()

        # Create a spec if one doesn't already exist
        if spec_rslt is None:
            spec_rslt = model.Specification(
                name=unicode(iface.__name__),
                documentation=unicode(iface.__doc__),
                title=unicode(getattr(iface, '__title__', None)),
                description=unicode(getattr(iface, '__description__', None)),
                )

            if hasattr(iface, '__is_tabable__'):
                spec_rslt.is_tabable = getattr(iface, '__is_tabable__')

            # Handle base classes
            for ibase in iface.__bases__:
                # only associate with interfaces that are also marked as part
                # of the data store schemata
                if ibase.extends(Schema):
                    base_rslt = Session.query(model.Specification)\
                        .filter_by(name=unicode(ibase.__name__))\
                        .first()

                    if base_rslt is None:
                        raise Exception(
                            '%s extends a base (%s) interface that is  not in '
                            'the data store' % (iface, ibase)
                            )

                    spec_rslt.bases.append(base_rslt)

        schema_rslt = model.Schema(specification=spec_rslt)

        for idependent in getattr(iface, '__dependents__', []):
            #
            # TODO: versioning
            #
            dependent_rslt = Session.query(model.Specification)\
                .filter_by(name=unicode(idependent.__name__))\
                .first()

            schema_rslt.specification.includes.append(dependent_rslt)

        attrs = {}

        # Now add/remove in all the changed fields
        for field_name, field_obj in zope.schema.getFieldsInOrder(iface):

            if field_name == u'state':
                continue

            if zope.schema.interfaces.IObject.providedBy(field_obj):
                # TODO link to versioned schema_obj.
                raise NotImplementedError('Don\'t supported nested objects yet')

            type_obj = field_obj

            is_list = zope.schema.interfaces.ICollection.providedBy(field_obj)

            if is_list:
                type_obj = field_obj.value_type

            is_choice = zope.schema.interfaces.IChoice.providedBy(type_obj)

            if is_choice:
                type_ = None
                for term in type_obj.vocabulary:
                    term_type = type(term.value)
                    if type_ is None or term_type == type_:
                        type_ = term_type
                    elif type_ != term_type:
                        raise Exception('All choice values must be same type')

                type_class = python_zope_map[type_]
            else:
                type_class = type_obj.__class__

            if type_class not in types:
                raise Exception(
                    '%s defines a field that is not supported: %s'
                    % (iface, type_class)
                    )

            type_name = types.getTerm(type_class).token

            type_rslt = Session.query(model.Type)\
                .filter_by(title=unicode(type_name))\
                .first()

            if field_obj.default is not None:
                default = unicode(field_obj.default)
            else:
                default = None

            attrs[field_name] = model.Attribute(
                name=unicode(field_name),
                order=field_obj.order,
                field=model.Field(
                    title=unicode(field_obj.title),
                    description=field_obj.description,
                    is_readonly=field_obj.readonly,
                    type=type_rslt,
                    is_list=is_list,
                    is_required=field_obj.required,
                    default=default
                    )
                )

            if is_choice:
                for i, term_obj in enumerate(type_obj.vocabulary, start=1):
                    attrs[field_name].field.choices.append(model.Choice(
                        name=term_obj.token,
                        title=term_obj.title,
                        value=unicode(term_obj.value),
                        order=i
                        ))

            schema_rslt.attributes.append(attrs[field_name])

        # The directives may have been loaded by plone, check that first
        tags = iface.queryTaggedValue('__form_directive_values__')

        if tags is None:
            tags = {}

            for tag in iface.getTaggedValueTags():
                tags[tag] = iface.getTaggedValue(tag)

        for key, item in tags.items():
            if key in directives:
                try:
                    if key is OMITTED_KEY:
                        for interface, field_name, value in item:
                            attrs[field_name].field.directive_omitted = value is 'true'
                    elif key is WIDGETS_KEY:
                        for field_name, module in item.items():
                            attrs[field_name].field.directive_widget = unicode(module)
                    elif key is MODES_KEY:
                        for interface, field_name, value in item:
                            attrs[field_name].field.directive_mode = unicode(value)
                    elif key is ORDER_KEY:
                        for field_name, order, target in item:
                            if order is 'before':
                                attrs[field_name].field.directive_before = value
                            elif order is 'after':
                                attrs[field_name].field.directive_after = value
                            else:
                                raise Exception('order %s is not supported'
                                                % order)
                    elif key is READ_PERMISSIONS_KEY:
                        for field_name, value in item.items():
                            attrs[field_name].field.directive_read = unicode(value)
                    elif key is WRITE_PERMISSIONS_KEY:
                        for field_name, value in item.items():
                            attrs[field_name].field.directive_write = unicode(value)
                    elif key is FIELDSETS_KEY:
                        for i, fieldset_obj in enumerate(item, start=1):
                            if fieldset_obj.description:
                                description = unicode(fieldset_obj.description)
                            else:
                                description = None

                            fieldset_rslt = model.Fieldset(
                                name=unicode(fieldset_obj.__name__),
                                label=unicode(fieldset_obj.label),
                                description=description,
                                order=i
                                )

                            for j, field_name in enumerate(fieldset_obj.fields, 1):
                                fieldset_rslt.fields.append(model.FieldsetItem(
                                    name=unicode(field_name),
                                    order=j
                                    ))

                            schema_rslt.fieldsets.append(fieldset_rslt)

                except KeyError as e:
                    # this will occur IF we don't actually have an attribute
                    # for the directive.
                    continue

        Session.add(schema_rslt)
        Session.flush()

        iface.__version__ = schema_rslt.create_date
        return iface


    def purge(self, key):
        Session = self._datastore.getScopedSession()


        num_instances = Session.query(model.Instance)\
                        .join(model.Schema.specification)\
                        .filter_by(module=self._module)\
                        .count()

        if num_instances > 0:
            raise Exception('There is already data stored for %s' % self._module)

        schema_rslt = Session.query(model.Schema)\
                      .join(model.Specification)\
                      .filter_by(module=self._module)\
                      .first()

        Session.remove(schema_rslt)
        Session.flush()


    def retire(self, key):
        # Will fail, schema managers cannot be 'retired'.
        # TODO: why?
        raise Exception('Can\'t retire schemata')
