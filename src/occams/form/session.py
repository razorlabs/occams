
from zope.component import getUtilitiesFor
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary

from five import grok
from z3c.saconfig.interfaces import IScopedSession
from z3c.saconfig import named_scoped_session

from occams.form import MessageFactory as _
from occams.form.interfaces import IRepository


@grok.adapter(IRepository)
@grok.implementer(IScopedSession)
def getRespositorySession(context):
    """
    Retrieves the session specified by the repository
    """
    return named_scoped_session(context.session)


class AvailableSessions(grok.GlobalUtility):
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
