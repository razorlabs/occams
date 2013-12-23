from pyramid import testing

from occams.clinical import Session, RosterSession, models
from occams.clinical.compat import configparser
from occams.datastore import model as datastore
from occams.roster import model as roster


config = configparser.ConfigParser()


class ClinicalModelFixture(object):

    def setUp(self):
        Session.begin()

    def tearDown(self):
        Session.rollback()


class ClinicalFunctionalFixture(object):

    def setUp(self):
        from occams.clinical import main
        from webtest import TestApp
        app = main({})
        self.testapp = TestApp(app)
        testing.setUp()

    def tearDown(self):
        empty_db()
        testing.tearDown()


def empty_db():
    """
    Truncate database tables.
    """
    for mapping in (
            models.Patient, models.Study,
            datastore.Schema,
            datastore.User):
        Session.query(mapping).delete(False)
    Session.commit()
