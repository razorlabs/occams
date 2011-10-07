from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.testing import IntegrationTesting
from plone.app.testing import FunctionalTesting

from zope.configuration import xmlconfig

from avrc.data.store.testing import DATABASE_LAYER


class HiveFormSandBoxLayer(PloneSandboxLayer):

    defaultBases = (DATABASE_LAYER,)

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import hive.form as package
        xmlconfig.file('configure.zcml', package, context=configurationContext)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'hive.form:default')


HIVE_FORM_FIXTURE = HiveFormSandBoxLayer()

HIVE_FORM_INTEGRATION_TESTING = IntegrationTesting(
    bases=(HIVE_FORM_FIXTURE,),
    name='hive.form:Integration'
    )

HIVE_FORM_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(HIVE_FORM_FIXTURE,),
    name='hive.form:Functional'
    )
