from Products.CMFCore.utils import getToolByName
from occams.form import Logger as default_logger

PROFILE_ID = u'profile-occams.form:default'

def import_(context, logger=default_logger):
    portal_setup = getToolByName(context, 'portal_setup')
    portal_setup.runImportStepFromProfile(PROFILE_ID, 'cssregistry')
    portal_setup.runImportStepFromProfile(PROFILE_ID, 'jsregistry')
    portal_setup.runImportStepFromProfile(PROFILE_ID, 'typeinfo')
