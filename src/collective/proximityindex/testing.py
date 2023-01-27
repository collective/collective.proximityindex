# -*- coding: utf-8 -*-
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import (
    applyProfile,
    FunctionalTesting,
    IntegrationTesting,
    PLONE_FIXTURE,
    PloneSandboxLayer,
)
from plone.testing import z2

import collective.proximityindex


class CollectiveProximityindexLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        import plone.app.dexterity
        self.loadZCML(package=plone.app.dexterity)
        import plone.restapi
        self.loadZCML(package=plone.restapi)
        self.loadZCML(package=collective.proximityindex)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'collective.proximityindex:default')


COLLECTIVE_PROXIMITYINDEX_FIXTURE = CollectiveProximityindexLayer()


COLLECTIVE_PROXIMITYINDEX_INTEGRATION_TESTING = IntegrationTesting(
    bases=(COLLECTIVE_PROXIMITYINDEX_FIXTURE,),
    name='CollectiveProximityindexLayer:IntegrationTesting',
)


COLLECTIVE_PROXIMITYINDEX_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(COLLECTIVE_PROXIMITYINDEX_FIXTURE,),
    name='CollectiveProximityindexLayer:FunctionalTesting',
)


COLLECTIVE_PROXIMITYINDEX_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        COLLECTIVE_PROXIMITYINDEX_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE,
    ),
    name='CollectiveProximityindexLayer:AcceptanceTesting',
)
