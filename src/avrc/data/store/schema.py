"""
Responsible for schemata, attributes, and vocabularies

Additionally, we support plone.directives.form
"""

from datetime import datetime, date, time

from zope.component import adapts
from zope.component import getUtility
from zope.interface import implements
from zope.interface.interface import InterfaceClass
from zope.interface import alsoProvides
from zope.i18nmessageid import MessageFactory
import zope.schema

from plone.alterego import dynamic

from sqlalchemy import func

from avrc.data.store import interfaces
from avrc.data.store import model

_ = MessageFactory(__name__)

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

def SupportedTypesVocabularyFactory(context=None):
    """
    Generates a list of supported types. This is used for auto-generating
    meta data into the data store once it is added into a site.
    """
    return supported_types_vocabulary

alsoProvides(SupportedTypesVocabularyFactory,
             zope.schema.interfaces.IVocabularyFactory)


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

class MutableSchema(object):
    """
    This module is in charge of controlling the actual properties of the
    target module. It's sole purpose is for writing, not retrieving properties.
    """

    implements(interfaces.IMutableSchema)

    _module = None

    _version = None

    # Don't lose the session
    _session = None

    # The working schema
    _schema_rslt = None

    # list of items already changed (can't change more than on in a
    # transaction). if the item is not in this list, it is assumed unchanged
    # and copied over from the previous version.
    _attributes = list()
    _invariants = list()

    def __init__(self, module, version=None):
        """
        Constructor
        """
        self._module = unicode(module)
        self._version = version

        self._session = Session = getUtility(interfaces.ISessionFactory)()
        self._session.begin()

        spec_rslt = Session.query(model.Specification)\
                    .filter_by(module=self._module)\
                    .first()

        self._schema_rslt = model.Schema(specification=spec_rslt)


    @classmethod
    def fromInterface(cls):
        """
        TODO
        """

    def __del__(self):
        """
        Destructor (NOT FOR python del command...)
        """
        # Rollback any unsaved changes
        self._session.rollback()

    def create_invariant(self, name):
        """
        """
        if name in self._changed:
            raise Exception("Can't change %s more than once in the "
                            "same version" % name)

        name = unicode(name)
        Session = self._session

        if name in self._invariants:
            raise Exception("Can't change %s more than once in the "
                            "same version" % name)

        self._schema_rslt.invariants.append(model.Invariant(name=name))
        self._invariants.append(name)

    def remove_invariant(self, name):
        """
        """
        name = unicode(name)
        if name in self._invariants:
            raise Exception("Can't change %s more than once in the "
                            "same version" % name)
        self._invariants.append(name)

    def revert_attribute(self, key, version):
        """
        Reverts the attribute to a specific version. Not that this will
        actually upgrade the schema, but the attribute will be restored the
        said  version.
        """

    def __setitem__(self, name, value):
        """
        @param key: the name of the property to change
        @param value: the zope schema value to set for the property, None to
                      remove the property
        """
        name = unicode(name)
        field_obj = value
        Session = self._session

        if name in self._attributes:
            raise Exception("Can't change %s more than once in the "
                            "same version" % name)

        if value is not None:
            term_obj = supported_types_vocabulary.getTerm(field_obj.__class__)

            if term_obj is None:
                raise Exception("Not supported: %s" % str(field_obj.__class__))

            type_rslt = Session.query(model.Type)\
                        .filter_by(title=unicode(term_obj.token))\
                        .first()

            self._schema_rslt.attributes.append(model.Attribute(
                name=name,
                is_invariant=False,
                order=field_obj.order,
                field=model.Field(
                    title=unicode(field_obj.title),
                    description=unicode(field_obj.description),
                    type=type_rslt,
                    is_required=field_obj.required,
                    )
                ))

        self._attributes.append(name)
        Session.flush()

    def save(self):
        """
        Commits its changes to the back-end. Expires the current instance.
        """
        Session = self._session

        if Session is None:
            raise Exception("expired")

        schema_old_rslt = Session.query(model.Schema)\
                          .filter_by(create_date=self._version)\
                          .join(model.Specification)\
                          .filter_by(module=self._module)\
                          .first()

        for attribute_rslt in schema_old_rslt.attributes:
            # Copy the properties from the last version if they haven't been
            # changed
            if attribute_rslt.name not in self._attributes:
                self._schema_rslt.attributes.append(model.Attribute(
                    name=attribute_rslt.name,
                    is_invariant=False,
                    order=attribute_rslt.order,
                    field=attribute_rslt.field
                    ))

        for invariant_rslt in schema_old_rslt.invariants:
            if invariant_rslt.name not in self._invariants:
                self._schema_rslt.invariants.append(model.Invariant(
                    name=invariant_rslt.name
                    ))

        Session.add(self._schema_rslt)
        Session.commit()
        self._session = None

class SchemaManager(object):
    """
    """
    implements(interfaces.ISchemaManager)

    def __init__(self):
        """
        """

    def save(self, target):
        """
        """
        Session = getUtility(interfaces.ISessionFactory)()
        Session.commit()

    def put(self, source):
        """
        TODO: maybe upgrade an existing one if it's already in the database?
                Can't because we don't know how to to tell if it has changed?

        @param source: A ZOPE interface specification
        """
        Session = getUtility(interfaces.ISessionFactory)()

        title = unicode(source.__name__)
        desc = unicode(source.__doc__)

        # If we don't already have a specification, we'll start a new schema
        spec_rslt = Session.query(model.Specification)\
                    .filter_by(title=title)\
                    .first()

        if spec_rslt is None:
            spec_rslt = model.Specification(title=title, description=desc)

        # Upgrade the specification
        schema_rslt = model.Schema()
        schema_rslt.specification = spec_rslt

        for name, field in zope.schema.getFieldsInOrder(source):
            name = unicode(name)
            attribute_rslt = Session.query(model.Attribute)\
                             .filter_by(name=name)\
                             .join(model.Schema.specification)\
                             .filter_by(title=title)\
                             .first()

            if attribute_rslt is None:
                attribute_rslt = model.Attribute(
                    name=name,
                    title=field.title,
                    description=field.description,
                    is_required=field.required,
                    order=field.order
                    )

            type_rslt = Session.query(model.Type)\
                        .filter_by(title=_utils.TYPE_2_STR[field.__class__])\
                        .first()

            attribute_rslt.type = type_rslt

            schema_rslt.attributes.append(attribute_rslt)

        Session.add(schema_rslt)
        Session.commit()

    def get(self, module, version=None):
        """
        @see: avrc.data.store.interfaces.ISchemaManager#getSchema
        """
        module = unicode(module)
        Session = getUtility(interfaces.ISessionFactory)()

        schema_q = Session.query(model.Schema)\
                  .join(model.Specification)\
                  .filter_by(module=module)

        if version is not None:
            schema_q = schema_q.filter(model.Schema.create_date==version)

        schema_rslt = schema_q.first()


        if schema_rslt is None:
            return None

        attrs = {}

        for attribute_rslt in schema_rslt.attributes:
            cls = _utils.STR_2_TYPE[attribute_rslt.type.title]
            attrs[attribute_rslt.name] = cls(
                title=attribute_rslt.title,
                description=attribute_rslt.description,
                required=attribute_rslt.is_required
                )

        klass = InterfaceClass(
            name=schema_rslt.title,
            __doc__=schema_rslt.description,
            __module__="avrc.data.store.generated",
            bases=(interfaces.IMutableSchema,),
            attrs=attrs,
            )

        return klass

    def modify(self, target):
        """
        It isn't very clear how the modification of schemata is going to work.
        That is, how will be know which parts of the schema have been changed?
        """
        raise NotImplementedError()

    def expire(self, target):
        """
        """
        raise Exception(u"Expiring of schema is not allowed")

    def remove(self, key, hard=False):
        """
        Removes a
        """
        title = unicode(key)
        Session = getUtility(interfaces.ISessionFactory)()

        num_instances = Session.query(model.Instance)\
                        .join(model.Schema.specification)\
                        .filter_by(title=title)\
                        .count()

        if num_instances > 0 and not hard:
            raise Exception("There is already data stored for %s" % key)

        schema_rslt = Session.query(model.Schema)\
                      .join(model.Specification)\
                      .filter_by(title=title)\
                      .first()

        Session.remove(schema_rslt)
        Session.commit()

    def list(self):
        """
        Returns a list of all the existing schemata NAMES only.
        """
        Session = getUtility(interfaces.ISessionFactory)()
        return Session.query(model.Specification.title).all()
