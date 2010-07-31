import unittest

from sqlalchemy import orm, create_engine

from avrc.data.store import model
import etc

Session = orm.scoped_session(orm.sessionmaker(
    autoflush=True,
    autocommit=False,
#    twophase=True
    ))

Session.configure(bind=create_engine("sqlite:///:memory:", echo=etc.SA_ECHO))

model.setup(Session.bind)

class TestCase(unittest.TestCase):

    def setUp(self):
        """"""
#        Session.begin()
#        Session.begin_nested()
#        pass

    def tearDown(self):
        """"""
#        Session.rollback()
#        Session.commit()

    def test_specification(self):
        """
        """

        session = Session()
        session.add(model.Specification(title=u"IFoo")
        session.add(model.Specification(title=u"IBar")
        session.add(model.Specification(title=u"IBaz")

        session.begin_nested() # establish a savepoint
        session.add(model.Specification(title=u"IDummy")
        session.rollback()  # rolls back u3, keeps u1 and u2

        session.commit() # commits u1 and u2


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
