"""
Unit testing resources
"""

import os
import tempfile

import sqlalchemy as sa
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.testing import IntegrationTesting
from plone.app.testing import FunctionalTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import TEST_USER_ID
import zope.component
from z3c import saconfig

from occams.datastore import model as datastore
from occams.form.saconfig import EventAwareScopedSession


ENGINE_NAME = u'occams.form.testing.Engine'
SESSION_NAME = u'occams.form.testing.Session'


class OccamsFormSandBoxLayer(PloneSandboxLayer,):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        import occams.form as package
        self.loadZCML(package=package)

        # setup the database utilities
        fileno, self.databaseFileName = tempfile.mkstemp(suffix='.db')
        uri = 'sqlite:///%s' % self.databaseFileName

        # we don't actually need the engine, just the uri for the utilities
        datastore.DataStoreModel.metadata.create_all(sa.create_engine(uri))
        engineUtility = saconfig.EngineFactory(uri)
        sessionUtility = EventAwareScopedSession(engine=ENGINE_NAME)
        zope.component.provideUtility(engineUtility, name=ENGINE_NAME)
        zope.component.provideUtility(sessionUtility, name=SESSION_NAME)

        session = saconfig.named_scoped_session(SESSION_NAME)

        # add the test users
        session.add(datastore.User(key=TEST_USER_ID))
        session.flush()

    def tearDownZope(self, app):
        os.unlink(self.databaseFileName)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'occams.form:default')


OCCAMS_FORM_FIXTURE = OccamsFormSandBoxLayer()

OCCAMS_FORM_INTEGRATION_TESTING = IntegrationTesting(
    bases=(OCCAMS_FORM_FIXTURE,),
    name='OccamsForm:Integration'
    )

OCCAMS_FORM_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(OCCAMS_FORM_FIXTURE,),
    name='OccamsForm:Functional'
    )
