from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.testing import IntegrationTesting
from plone.app.testing import FunctionalTesting

from zope.configuration import xmlconfig

from avrc.data.store.testing import DATABASE_LAYER


class OccamsFormSandBoxLayer(PloneSandboxLayer):

    defaultBases = (DATABASE_LAYER,)

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import occams.form as package
        xmlconfig.file('configure.zcml', package, context=configurationContext)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'occams.form:default')


OCCAMS_FORM_FIXTURE = OccamsFormSandBoxLayer()

OCCAMS_FORM_INTEGRATION_TESTING = IntegrationTesting(
    bases=(OCCAMS_FORM_FIXTURE,),
    name='occams.form:Integration'
    )

OCCAMS_FORM_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(OCCAMS_FORM_FIXTURE,),
    name='occams.form:Functional'
    )
