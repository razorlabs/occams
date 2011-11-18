"""
Database helper components
"""

from zope.component import getUtilitiesFor
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary

from five import grok
from z3c.saconfig.interfaces import IScopedSession

from occams.form import MessageFactory as _

class AvailableSessionsVocabularyFactory(grok.GlobalUtility):
    """
    Builds a vocabulary containing the Plone instance's registered 
    ``z3c.saconfig`` sessions.
    """
    grok.name(u'occams.form.AvailableSessions')
    grok.title(_(u'Available Sessions'))
    grok.description(_(u'A listing of registered z3c.saconfig sessions.'))
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        registered = getUtilitiesFor(IScopedSession)
        names = [name for name, utility in registered]
        return SimpleVocabulary.fromValues(names)
