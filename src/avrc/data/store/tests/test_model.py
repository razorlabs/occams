import unittest

import sqlalchemy as sa
from sqlalchemy import orm

from avrc.data.store import model
import etc

# For the sake of testings, let's control when objects are flushed to the db
Session = orm.scoped_session(orm.sessionmaker(
    autoflush=False,
    autocommit=False,
    # doesn't work in sqlite =\
#    twophase=True
    ))

dsn = "sqlite:///:memory:"
Session.configure(bind=sa.create_engine(dsn, echo=etc.SA_ECHO))

model.setup(Session.bind)

class TestCase(unittest.TestCase):
    """
    This testing module is mostly to make sure that the model setup makes
    sense programatically (i.e. it's not awkward to use)
    """

    def setUp(self):
        try:
            # Auto-transaction should b1e in place, but try it anyways
            Session.begin()
        except sa.exceptions.InvalidRequestError:
            pass

    def tearDown(self):
        # Remove the transaction so each test case is working with fresh data
        Session.rollback()

    def test_specification(self):
        """
        Make sure the specification module is working properly
        """

        # Test arguments
        Session.add(model.Specification(
            module=u"some.random.package.IModule",
            documentation=u"Some random blurb.",
            title=u"Dummy Module",
            description=u"Dummy Module User-Friendly",
            is_association=False,
            is_virtual=False,
            is_eav=False
            ))
        Session.rollback()

        # Test that module and documentation (both) can't be null
        Session.add(model.Specification(module=None, documentation=None))
        self.assertRaises(sa.exceptions.IntegrityError, Session.flush)
        Session.rollback()

        # Test that module can't be null
        Session.add(model.Specification(module=u"stuff.Stuff",
                                        documentation=None))
        self.assertRaises(sa.exceptions.IntegrityError, Session.flush)
        Session.rollback()

        # Test that documentation can't be null
        Session.add(model.Specification(module=None, documentation=u"Stuff"))
        self.assertRaises(sa.exceptions.IntegrityError, Session.flush)
        Session.rollback()

        # Test uniqueness of the specification
        Session.add(model.Specification(module=u"FOO", documentation=u"..."))
        Session.add(model.Specification(module=u"FOO", documentation=u"..."))
        self.assertRaises(sa.exceptions.IntegrityError, Session.flush)
        Session.rollback()

    def test_hierarchy(self):
        """
        Make sure class parent/child relationships are working properly
        """
        # Child -> Parent -> Grandparent
        grandparent = model.Specification(module=u"Grandparent A" ,
                                          documentation=u"")
        parent = model.Specification(module=u"Parent",documentation=u"")
        child = model.Specification(module=u"Child", documentation=u"")

        parent.bases.append(grandparent)
        child.bases.append(parent)
        Session.add_all([grandparent, parent, child])
        Session.flush()

        # Foo -> (Base1, Base2, Base3)
        base1 = model.Specification(module=u"Base1", documentation=u"")
        base2 = model.Specification(module=u"Base2", documentation=u"")
        base3 = model.Specification(module=u"Base3", documentation=u"")
        foo = model.Specification(module=u"Foo", documentation=u"")
        foo.bases.append(base1)
        foo.bases.append(base2)
        foo.bases.append(base3)
        Session.add(foo)
        Session.flush()

    def test_schema(self):
        """
        Make sure schemata are added properly
        """
        # Regular schema
        schema = model.Schema()
        schema.specification = model.Specification(module=u"test.Schema",
                                                   documentation=u"")
        Session.add(schema)
        Session.flush()
        Session.rollback()

        # Schema without specification (should fail)
        Session.add(model.Schema())
        self.assertRaises(sa.exceptions.IntegrityError, Session.flush)

    def test_attributes(self):
        """
        Test proper setup of attributes
        """
        # Create an empty schema
        schema = model.Schema()
        schema.specification = model.Specification(module=u"foo.Foo",
                                                   documentation=u"")
        Session.add(schema)
        Session.flush()

        # Add an empty property
        attribute = model.Attribute(name=u"bar")
        schema.attributes.append(model.Attribute(name=u"bar"))
        Session.flush()

        # Make sure new attributes default to non-invariants
        self.assertFalse(attribute.is_invariant)

        # Try to add it again
        schema.attributes.append(model.Attribute(name=u"bar"))
        self.assertRaises(sa.exceptions.IntegrityError, Session.flush)

    def test_field(self):
        """
        Test proper setup of fields
        """
        faketype = model.Type(title=u"Fake", description=u"Stuff")
        widget = model.Widget(module=u"foo.bar.baz")
        Session.add_all([faketype, widget])
        Session.flush()

        field = model.Field(
            title=u"Foo",
            description=u"Suff about foo",
            documentation=u"None one will see this...",
            is_searchable=True,
            is_required=True,
            is_inline_image=False,
            is_repeatable=False,
            minimum=1,
            maximum=2,
            width=100,
            height=80,
            url=u"http://google.com",
            type=faketype,
            widget=widget,
            )
        Session.add(field)
        Session.flush()

    def test_versioning(self):
        """
        Test full specification/schema/attribute/field combo
        """
        mytype = model.Type(title=u"Fakeness")
        Session.add_all([mytype])
        Session.flush()

        # Setup Version 1
        schema_old = model.Schema(
            specification=model.Specification(
                    module=u"test.Test",
                    documentation=u""
                    )
            )

        schema_old.attributes.append(model.Attribute(
            name=u"foo",
            field=model.Field(title=u"Foo", type=mytype),
            ))
        schema_old.attributes.append(model.Attribute(
            name=u"bar",
            field=model.Field(title=u"Bar", type=mytype),
            ))
        schema_old.attributes.append(model.Attribute(
            name=u"baz",
            field=model.Field(title=u"Baz", type=mytype),
            ))
        Session.add(schema_old)
        Session.flush()

        # Setup Version 2, remove baz
        schema_new = model.Schema(specification=schema_old.specification)
        for attribute in schema_old.attributes:
            # In order to create a new version we need to copy all
            # the attributes
            schema_new.attributes.append(model.Attribute(
                name=attribute.name,
                field=attribute.name != u"baz" and attribute.field or None,
                is_invariant=attribute.is_invariant,
                order=attribute.order,
                ))
        Session.add(schema_new)
        Session.flush()

        # Setup Version 3, add comment to bar
        schema_old = schema_new
        schema_new = model.Schema(specification=schema_old.specification)
        for attribute in schema_old.attributes:
            schema_new.attributes.append(model.Attribute(
                name=attribute.name,
                is_invariant=attribute.is_invariant,
                field=attribute.field,
                order=attribute.order,
                ))

            if attribute.name is u"bar":
                attribute.field = model.Field(
                    title=attribute.field.title,
                    description=u"....",
                    type=attribute.field.type
                    )
        Session.add(schema_new)
        Session.flush()
        Session.commit()

    def test_vocabulary(self):
        """
        Test proper setup of vocabularies and terms
        """

    def test_instance(self):
        """
        Test proper setup of instances.
        """

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
