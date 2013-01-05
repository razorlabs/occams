"""
Unit testing resources
"""

import sqlalchemy as sa
import plone.app.testing
from z3c import saconfig
from zope import component

from occams.datastore import model as datastore
from occams.form.saconfig import EventAwareScopedSession


ENGINE_NAME = u'occams.form.testing.Engine'
SESSION_NAME = u'occams.form.testing.Session'


class OccamsFormSandBoxLayer(plone.app.testing.PloneSandboxLayer):

    defaultBases = (plone.app.testing.PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        import occams.form as package
        self.loadZCML(package=package)

        # setup the database utilities
        engine_utility = saconfig.EngineFactory('sqlite://')
        component.provideUtility(engine_utility, name=ENGINE_NAME)
        session_utility = EventAwareScopedSession(engine=ENGINE_NAME)
        component.provideUtility(session_utility, name=SESSION_NAME)

        # add the test users
        session = saconfig.named_scoped_session(SESSION_NAME)
        datastore.DataStoreModel.metadata.create_all(session.bind)
        session.add(datastore.User(key=plone.app.testing.TEST_USER_ID))
        session.flush()

    def setUpPloneSite(self, portal):
        plone.app.testing.applyProfile(portal, 'occams.form:default')


OCCAMS_FORM_FIXTURE = OccamsFormSandBoxLayer()

OCCAMS_FORM_INTEGRATION_TESTING = plone.app.testing.IntegrationTesting(
    bases=(OCCAMS_FORM_FIXTURE,),
    name='OccamsForm:Integration'
    )

OCCAMS_FORM_FUNCTIONAL_TESTING = plone.app.testing.FunctionalTesting(
    bases=(OCCAMS_FORM_FIXTURE,),
    name='OccamsForm:Functional'
    )
