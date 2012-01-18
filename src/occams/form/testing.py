"""
Unit testing resources
"""

from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.testing import IntegrationTesting
from plone.app.testing import FunctionalTesting

from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login
from plone.app.testing import setRoles

import os
import tempfile
from zope.component import provideUtility
from z3c.saconfig import EngineFactory
from z3c.saconfig import GloballyScopedSession
from sqlalchemy import create_engine

from avrc.data.store import model


ENGINE_NAME = u'occams.form.testing.Engine'
SESSION_NAME = u'occams.form.testing.Session'


class OccamsFormSandBoxLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        import occams.form as package
        self.loadZCML(package=package)

        # Setup the database utilities
        fileno, self.databaseFileName = tempfile.mkstemp(suffix='.db')
        uri = 'sqlite:///%s' % self.databaseFileName
        # we don't actually need the engine, just the uri for the utilities
        model.Model.metadata.create_all(create_engine(uri))
        engineUtility = EngineFactory(uri)
        sessionUtility = GloballyScopedSession(engine=ENGINE_NAME)
        provideUtility(engineUtility, name=ENGINE_NAME)
        provideUtility(sessionUtility, name=SESSION_NAME)

    def tearDownZope(self, app):
        os.unlink(self.databaseFileName)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'occams.form:default')

        # Add test content
        setRoles(portal, TEST_USER_ID, ['Manager'])
        login(portal, TEST_USER_NAME)
        portal.invokeFactory('occams.form.repository', 'test-repository',
            title=u'Test Repository',
            session=SESSION_NAME
            )
        setRoles(portal, TEST_USER_ID, ['Member'])


OCCAMS_FORM_FIXTURE = OccamsFormSandBoxLayer()

OCCAMS_FORM_INTEGRATION_TESTING = IntegrationTesting(
    bases=(OCCAMS_FORM_FIXTURE,),
    name='OccamsForm:Integration'
    )

OCCAMS_FORM_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(OCCAMS_FORM_FIXTURE,),
    name='OccamsForm:Functional'
    )
