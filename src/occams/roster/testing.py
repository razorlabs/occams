u"""
Application layers
"""

import plone.app.testing as plone
from zope.configuration import xmlconfig
from zope import component
from z3c import saconfig

from occams.roster import model
from occams.roster import Session


class OccamsRosterLayer(plone.PloneSandboxLayer):

    defaultBases = (plone.PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import occams.roster as package
        xmlconfig.file('configure.zcml', package, context=configurationContext)

        engine_uri = u'sqlite:///:memory:'
        engine_name = u'test.RosterEngine'
        session_name = u'occams.roster.Session'

        engine_utility = saconfig.EngineFactory(engine_uri)
        component.provideUtility(engine_utility, name=engine_name)
        session_utility = saconfig.GloballyScopedSession(engine=engine_name)
        component.provideUtility(session_utility, name=session_name)

    def setUpPloneSite(self, portal):
        plone.applyProfile(portal, 'occams.roster:default')


OCCAMS_ROSTER_FIXTURE = OccamsRosterLayer()

OCCAMS_ROSTER_INTEGRATION_TESTING = plone.IntegrationTesting(
    bases=(OCCAMS_ROSTER_FIXTURE,),
    name='OccamsRoster:Integration'
    )

OCCAMS_ROSTER_FUNCTIONAL_TESTING = plone.FunctionalTesting(
    bases=(OCCAMS_ROSTER_FIXTURE,),
    name='OccamsRoster:Functional'
    )

