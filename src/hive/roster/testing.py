""" 
Application layers
"""

from zope.configuration import xmlconfig
from zope.component import provideUtility

from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import IntegrationTesting
from plone.app.testing import FunctionalTesting

from z3c.saconfig.utility import EngineFactory
from z3c.saconfig.utility import GloballyScopedSession
from z3c.saconfig import named_scoped_session

from hive.roster import model


def clearModelData():
    """
    Helper method to clear model data that might have been created through
    transaction commits.
    """
    session = named_scoped_session('hive.roster.Session')
    session.query(model.Site).delete()
    session.query(model.Identifier).delete()
    session.commit()


class OccamsRosterLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import hive.roster as package
        xmlconfig.file('configure.zcml', package, context=configurationContext)

        sessions = (
            (u'hive.roster.Session', 'test.RosterEngine', 'sqlite:///:memory:'),
            )

        for (sessionName, engineName, uri) in sessions:
            engineUtility = EngineFactory(uri)
            provideUtility(engineUtility, name=engineName)
            sessionUtility = GloballyScopedSession(engine=engineName)
            provideUtility(sessionUtility, name=sessionName)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'hive.roster:default')


OCCAMS_ROSTER_FIXTURE = OccamsRosterLayer()

OCCAMS_ROSTER_INTEGRATION_TESTING = IntegrationTesting(
    bases=(OCCAMS_ROSTER_FIXTURE,),
    name='OccamsRoster:Integration'
    )

OCCAMS_ROSTER_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(OCCAMS_ROSTER_FIXTURE,),
    name='OccamsRoster:Functional'
    )
