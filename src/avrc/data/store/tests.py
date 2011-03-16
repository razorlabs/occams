import unittest

from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject
import zope.schema
import zope.interface

from plone.directives import form

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

from avrc.data.store import model
from avrc.data.store import Datastore
from avrc.data.store.interfaces import IDatastore
from avrc.data.store.interfaces import IDatastoreFactory
from avrc.data.store.interfaces import IManagerFactory
from avrc.data.store.interfaces import ISchemaManager
from avrc.data.store.schema import DatastoreSchemaManager
from avrc.data.store import Schema


class INotImportant(zope.interface.Interface):
    pass


class ISimple(Schema, INotImportant):
    """ OBJECT SCHEMAZ """


class IStandaloneInterface(Schema):
    """ This is very simple stanalone interface. """

    foo = zope.schema.TextLine(
        title=u'Foo',
        description=u'Something about foo.',
        required=False
        )

    bar = zope.schema.Text(
        title=u'Bar',
        description=u'Something about bar.',
        default=u'Something\nReally Long'
        )

    baz = zope.schema.Int(
        title=u'Baz',
        description=u'Something about baz.',
        default=420
        )

    joe = zope.schema.List(
        title=u'Joe',
        description=u'A little hard',
        value_type=zope.schema.Choice(
            values=['apples', 'bananas', 'strawberries', 'jello']
            )
        )


class IDependentInterface(Schema):
    """ as;dlfjasd;fjfasd;fsad """

setattr(IDependentInterface, '__dependents__', (ISimple, IStandaloneInterface,))


class IComposedInterface(Schema):
    """ This class contains annotations which SHOULD be saved as well... """

    integer = zope.schema.Int(
        title=u'INTEGER',
        description=u'INTEGERDESC'
        )

    object = zope.schema.Object(
        title=u'OBJECT',
        description=u'OBJECTDESC',
        schema=ISimple
        )


class IAnnotatedInterface(Schema):
    """ This is a dummy schema to test if the schema manger can properly
        import it. Also this class contains annotations which SHOULD be
        saved as well...
    """

    form.fieldset('results',
        label=u'Physical Exam Results',
        fields=['integer', 'text'])

    form.mode(integer='hidden')
    integer = zope.schema.Int(
        title=u'INTEGER',
        description=u'INTEGERDESC'
        )

    form.omitted('ommitme')
    ommitme = zope.schema.Int(
        title=u'OMITME',
        description=u'PLEASE'
        )

    form.widget(text='plone.app.z3cform.wysiwyg.WysiwygFieldWidget')
    text = zope.schema.Text(
        title=u'TEXT',
        description=u'TEXTDESC',
        )

    form.order_before(string='text')
    string = zope.schema.TextLine(
        title=u'STRING',
        description=u'STRINGDESC'
        )

    form.order_after(boolean='decimal')
    boolean = zope.schema.Bool(
        title=u'BOOL',
        description=u'BOOLDESC'
        )

    form.write_permission(decimal='cmf.ModifyPortalContent')
    decimal = zope.schema.Float(
        title=u'DECIMAL',
        description=u'DECIMALDESC'
        )

    form.mode(date='hidden')
    form.write_permission(date='cmf.ModifyPortalContent')
    date = zope.schema.Date(
        title=u'DATE',
        description=u'DATE'
        )


class IChoicedInterface(Schema):
    """ This simply tests that a vocabulary """

    choice = zope.schema.Choice(
            title=u'LISTCHOICE',
            values=('foo', 'bar', 'go' 'away', 'plz',)
        )


class IListInterface(Schema):
    """ A schema that contains lists. """

    int_list = zope.schema.List(
        title=u'Int List',
        value_type=zope.schema.Int(title=u'Int')
        )

    choice_list = zope.schema.List(
        title=u'Choice List',
        value_type=zope.schema.Choice(values=['foo', 'bar', 'baz'])
        )


class IGrandfather(Schema):
    pass


class IGrandmother(Schema):
    pass


class IFather(IGrandfather, IGrandmother):
    pass


class IUncle(IGrandfather, IGrandmother):
    pass


class IAunt(IGrandfather, IGrandmother):
    pass


class IBrother(IFather):
    pass


class ISister(IFather):
    pass


class TestCase(unittest.TestCase):

    def setUp(self):
        engine = create_engine(u'postgresql://test@localhost/test')
        self.session = scoped_session(sessionmaker(engine))
        model.Model.metadata.drop_all(self.session.bind, checkfirst=True)
        model.Model.metadata.create_all(self.session.bind, checkfirst=True)


    def tearDown(self):
        model.Model.metadata.drop_all(self.session.bind, checkfirst=True)


class DatastoreTestCase(TestCase):

    def test_implementation(self):
        """ Tests if the data store implementation has fully objected the
            interface contract.
        """
        self.assertTrue(verifyClass(IDatastore, Datastore))
        self.assertTrue(verifyObject(IDatastoreFactory, Datastore))

#
#    def test_add_instance(self):
#        """ Tests that data store is able to successfully add an object instance
#        """
#        ds = datastore.Datastore(session=u'')
#
#        sm = ds.getSchemaManager()
#
#        sm.put(IStandaloneInterface)
#        sm.put(ISimple)
#        sm.put(IAnnotatedInterface)
#
#        iface = sm.get(IStandaloneInterface.__name__)
#
#        obj = ds.spawn(iface,
#            foo=u'Hello World!',
#            bar=u'Really\n\n\nlong',
#            baz=123
#            )
#
#        key = ds.put(obj)
#
#        ds.get('avrc.data.store.schema.virtual.IStandaloneInterface')
#
#    def test_choiced_instance(self):
#        """
#        """
#        ds = datastore.Datastore(session=u'')
#
#        sm = ds.schemata
#
#        sm.put(IChoicedInterface)
#
#        iface = sm.get(IChoicedInterface.__name__)
#
#        obj = ds.spawn(iface, choice=u'foo')
#
#        ds.put(obj)
#
#        self.fail('OMG')
#
#    def test_update_data(self):
#        ds = datastore.Datastore(session=u'')
#        sm = ds.schemata
#
#        isource = IStandaloneInterface
#
#        sm.put(isource)
#
#        iface = sm.get(isource.__name__)
#
#        spawned = ds.spawn(iface,
##            foo=u'Before update',
##            bar=u'This is text before\nwe update',
##            baz=123,
##            joe=['jello', 'apples']
#            )
#
#        print 'spawned'
#        print spawned.__dict__
#
#        obj = ds.put(spawned)
#
#        print 'putted'
#        print obj.__dict__
#
#        gotten = ds.get(obj)
#
#        print 'gotten'
#        print gotten.__dict__
#
#        obj.foo = u'After update'
#        obj.bar = u'Now let\'s see it\nthis actually worked'
#        obj.baz = 987
#        obj.joe = ['apples', 'bananas']
#        print 'modified'
#        print obj.__dict__
#
#        obj = ds.put(obj)
#        print 'putted'
#        print obj.__dict__
#
#        self.fail('List interface test complete')
#
#    def test_list_schemata(self):
#        ds = datastore.Datastore(session=u'')
#        sm = ds.schemata
#
#        sm.put(IListInterface)
#
#        iface = sm.get(IListInterface.__name__)
#
#        obj = ds.put(ds.spawn(iface, int_list=[1,5,10], choice_list=['foo', 'baz']))
#
#        print obj
#        gotten = ds.get(obj)
#        print gotten.__dict__
#
#        self.fail('List interface test complete')
#
#
class SchemaManagementTestCase(TestCase):

    def test_implementation(self):
        """ Make sure the schema manager is fully implemented
        """
        self.assertTrue(verifyClass(ISchemaManager, DatastoreSchemaManager))
        self.assertTrue(verifyObject(IManagerFactory, DatastoreSchemaManager))
#
#    def test_add_name(self):
#        """ Make sure we can create a name.
#        """
#        manager = schema.DatastoreSchemaManager(DummyDatastore())
#
#    def test_schema_import(self):
#        """ Tests that the schema manager can properly import a schema into the
#            data store. The way it does this is it import the schema into the
#            data store, retrieves it and then checks if it's equivalent.
#        """
#        itest = IStandaloneInterface
#
#        schema.MutableSchema.import_(itest)
#
#        klass = schema.MutableSchema.get_interface(itest.__name__)
#
#        self.assertTrue(isinstance(klass, InterfaceClass))
#        self.assertTrue(klass.isOrExtends(interfaces.IMutableSchema))
#        self.assertEquals(klass.__name__, itest.__name__)
#        self.assertEquals(schema.virtual.__name__, klass.__module__)
#
#        # Check to make sure the generated interface still specifies the
#        # correct fields
#        dummynames = set(zope.schema.getFieldNames(itest))
#        klassnames = set(zope.schema.getFieldNames(klass))
#        self.assertTrue(set(dummynames) < set(klassnames))
#
#        # Check that we can properly recreate the fields also
#        for name in dummynames:
#            self.assertEquals(klass[name], itest[name])
#
#    def test_composite_import(self):
#        """ Test a schema that contains a object field to a another schema
#        """
#
#        itest = IComposedInterface
#
#        self.assertRaises(interfaces.UndefinedSchemaError,
#                          schema.MutableSchema.import_,
#                          itest)
#
#        schema.MutableSchema.import_(ISimple)
#        schema.MutableSchema.import_(IComposedInterface)
#
#        # TODO check this
#
#    def test_vocabulary_import(self):
#        """
#        """
#
#    def test_annotated_import(self):
#        """
#        """
#        itest = IAnnotatedInterface
#        schema.MutableSchema.import_(itest)
#
#        # Make sure the annotations are intact
#        klass = schema.MutableSchema.get_interface(itest.__name__)
#
#        from pprint import pprint
#
#        pprint(itest.queryTaggedValue('__form_directive_values__'))
#        pprint(klass.queryTaggedValue('__form_directive_values__'))
#
#    def test_versioning(self):
#        """
#        """
#
#    def test_dependents(self):
#        """
#        """
#        #dsn = u'sqlite:///test.db'
#        dsn = u'sqlite:///:memory:'
#        ds = datastore.Datastore(title=u'my ds', dsn=dsn)
#
#        sm = ds.schemata
#
#        sm.put(ISimple)
#        sm.put(IStandaloneInterface)
#        sm.put(IDependentInterface)
#
#        iface = sm.get(IDependentInterface.__name__)
#
#        for dependent in iface.__dependents__:
#            print dependent
#
#        #ds.put(obj)
#
#        self.fail('OMG')
#
#    def test_directives(self):
#        dsn = u'sqlite:///test.db'
#        #dsn = u'sqlite:///:memory:'
#        ds = datastore.Datastore(title=u'my ds', dsn=dsn)
#
#        sm = ds.schemata
#
#        sm.put(IAnnotatedInterface)
#
#        from pprint import pprint
#
#        print
#        print 'Original'
#        for tag in IAnnotatedInterface.getTaggedValueTags():
#            print tag
#            pprint(IAnnotatedInterface.getTaggedValue(tag))
#
#
#        pprint(IAnnotatedInterface.getTaggedValue('__form_directive_values__')['plone.supermodel.fieldsets'][0].__dict__)
#
#        iface = sm.get(IAnnotatedInterface.__name__)
#
#        print
#        print 'Generated'
#        for tag in iface.getTaggedValueTags():
#            print tag
#            pprint(iface.getTaggedValue(tag))
#
#
#        self.fail('OMG')
#
#    def test_inheritance(self):
#        """
#        """
#        dsn = u'sqlite:///test.db'
#        #dsn = u'sqlite:///:memory:'
#        ds = datastore.Datastore(title=u'blah', dsn=dsn)
#        sm = ds.schemata
#
#        sm.put(IGrandfather)
#        sm.put(IGrandmother)
#        sm.put(IFather)
#        sm.put(IUncle)
#        sm.put(IAunt)
#        sm.put(IBrother)
#        sm.put(ISister)
#
#        iface = sm.get(IGrandfather.__name__)
#        descendants = sm.get_descendants(iface)
#
#        print str(iface) + ' ' + str(iface.getBases())
#        print 'descendants:'
#        for descendant in descendants:
#            print str(descendant) + ' ' + str(descendant.getBases())
#
#        print
#
#        self.fail('Inheritance test complete')

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
