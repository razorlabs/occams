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

Session.configure(bind=sa.create_engine("sqlite:///:memory:",
                                        echo=etc.SA_ECHO))

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
        Session.add(model.Specification(module=None, documentation="Stuff"))
        self.assertRaises(sa.exceptions.IntegrityError, Session.flush)
        Session.rollback()

        # Test uniqueness of the specification
        Session.add(model.Specification(module="FOO", documentation=u"..."))
        Session.add(model.Specification(module="FOO", documentation=u"..."))
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



def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
