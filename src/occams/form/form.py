"""
Changeset tools
"""

from zope.component import getUtilitiesFor
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.vocabulary import SimpleTerm
from zope.lifecycleevent import IObjectAddedEvent
from zope.lifecycleevent import IObjectModifiedEvent

from five import grok

from avrc.data.store import model
from avrc.data.store.interfaces import IDataStore

from occams.form import MessageFactory as _
from occams.form import Logger as log
from occams.form.interfaces import IRepository


class FormsVocabularyFactory(grok.GlobalUtility):
    """
    Builds a vocabulary containing all the form names in the context
    """
    grok.name(u'occams.form.Forms')
    grok.title(_(u'Forms'))
    grok.description(_(u'A list of forms in the current context'))
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        if not IRepository.providedBy(context):
            raise Exception(_(u'Can only calculate forms for a repository'))
        datastore = IDataStore(context)
        session = datastore.session
        query = (
            session.query(model.Schema)
            .filter(model.Schema.asOf(None))
            .order_by(model.Schema.title)
            )
        terms = [SimpleTerm(s.name, title=s.title) for s in query.all()]
        return SimpleVocabulary(terms=terms)
