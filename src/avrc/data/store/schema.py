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
        self.__directives__ = {}
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

    def apply_directive(self, name, value):
        """
        """
        

    def revert_attribute(self, key, version):
        """
        Reverts the attribute to a specific version. Not that this will
        actually upgrade the schema, but the attribute will be restored the
        said  version.
        """

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

    def save(self):
        """
        Commits its changes to the back-end. Expires the current instance.
        """
        Session = getUtility(interfaces.ISessionFactory)()

        spec_rslt = Session.query(model.Specification)\
                    .filter_by(module=self.__module__)\
                    .first()

        # Create a spec if one doesn't already exist
        if spec_rslt is None:
            spec_rslt = model.Specification(
                module=self.__module__,
                documentation=self.__documentation__
                )

        schema_rslt = model.Schema(specification=spec_rslt)

        # Need toe old schema (if any) to copy over unchanged fields
        schema_old_rslt = Session.query(model.Schema)\
                          .filter_by(create_date=self.__version__)\
                          .join(model.Specification)\
                          .filter_by(module=self.__module__)\
                          .first()

        if schema_old_rslt is not None:
            for attribute_rslt in schema_old_rslt.attributes:
                # Copy unchanged properties from the last version
                if attribute_rslt.name not in self.__attributes__:
                    schema_rslt.attributes.append(model.Attribute(
                        name=attribute_rslt.name,
                        order=attribute_rslt.order,
                        field=attribute_rslt.field
                        ))

            for invariant_rslt in schema_old_rslt.invariants:
                if invariant_rslt.name not in self.__invariants__:
                    schema_rslt.invariants.append(model.Invariant(
                        name=invariant_rslt.name
                        ))

        # Now add/remove in all the changed fields
        for name, field_obj in self.__attributes__.items():
            if field_obj.__class__ not in supported_types_vocabulary:
                continue
                #Session.rollback()
                #raise Exception("Not supported: %s" % str(field_obj.__class__))

            term_obj = supported_types_vocabulary.getTerm(field_obj.__class__)

            type_rslt = Session.query(model.Type)\
                        .filter_by(title=unicode(term_obj.token))\
                        .first()

            schema_rslt.attributes.append(model.Attribute(
                name=name,
                order=field_obj.order,
                field=model.Field(
                    title=unicode(field_obj.title),
                    description=unicode(field_obj.description),
                    type=type_rslt,
                    is_required=field_obj.required,
                    )
                ))

        Session.add(schema_rslt)
        Session.commit()
        self.__attributes__ = {}
        self.__invariants__.clear()

    def delete(self, hard=False):
        """
        """
        Session = self._session

        num_instances = Session.query(model.Instance)\
                        .join(model.Schema.specification)\
                        .filter_by(module=self._module)\
                        .count()

        if num_instances > 0 and not hard:
            raise Exception("There is already data stored for %s" % self._module)

        schema_rslt = Session.query(model.Schema)\
                      .join(model.Specification)\
                      .filter_by(module=self._module)\
                      .first()

        Session.remove(schema_rslt)
        Session.commit()

    @classmethod
    def list(cls):
        """
        Returns a list of all the existing schemata module names only.
        """
        Session = getUtility(interfaces.ISessionFactory)()
        return Session.query(model.Specification.module).all()

    @classmethod
    def has_interface(cls, module, version=None):
        module = unicode(module)
        Session = getUtility(interfaces.ISessionFactory)()
        
        schema_q = Session.query(model.Schema)\
                  .join(model.Specification)\
                  .filter_by(module=module)

        if version is not None:
            schema_q = schema_q.filter(model.Schema.create_date==version)

        return schema_q.count() > 0

    @classmethod
    def get_interface(cls, module, version=None):
        """
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
            token = str(attribute_rslt.field.type.title)            
            field = supported_types_vocabulary.getTermByToken(token).value
            attrs[attribute_rslt.name] = field(
                title=attribute_rslt.field.title,
                description=attribute_rslt.field.description,
                required=attribute_rslt.field.is_required
                )

        klass = InterfaceClass(
            name=schema_rslt.specification.module,
            __doc__=schema_rslt.specification.documentation,
            __module__="avrc.data.store.schema.generated",
            bases=(interfaces.IMutableSchema,),
            attrs=attrs,
            )

        return klass

    @classmethod
    def import_(cls, interface):
        """
        @param source: A ZOPE interface specification
        """
        schema_obj = cls(module=unicode(interface.__name__),
                         documentation=unicode(interface.__doc__)
                         )

        for name, field in zope.schema.getFieldsInOrder(interface):
            schema_obj[unicode(name)] = field

        schema_obj.save()

