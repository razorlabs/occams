"""
Repository tools
"""

from zope.lifecycleevent import IObjectAddedEvent
from zope.lifecycleevent import IObjectModifiedEvent
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.vocabulary import SimpleTerm

from five import grok
from z3c.saconfig import named_scoped_session
from z3c.saconfig.interfaces import IScopedSession

from avrc.data.store import model
from avrc.data.store.upgrades import migrate
from avrc.data.store.interfaces import IDataStore

from occams.form import MessageFactory as _
from occams.form import Logger as log
from occams.form.interfaces import IRepository


MSG_INSALLING = _(u'Configuring "%(repository)s" at "%(url)s" (%(session)s)')


@grok.adapter(IRepository)
@grok.implementer(IScopedSession)
def getRespositorySession(context):
    """
    Retrieves the session specified by the repository
    """
    return named_scoped_session(context.session)


@grok.adapter(IRepository)
@grok.implementer(IDataStore)
def getRespositoryDataStore(context):
    """
    Retrieves the a datastore using the session specified by the repository
    """
    return IDataStore(named_scoped_session(context.session))


@grok.subscribe(IRepository, IObjectAddedEvent)
def handleRepositoryAddedEvent(item, event):
    """
    Sets up the database when a repository is created.
    """
    _configureRepositoryDataStore(item)


@grok.subscribe(IRepository, IObjectModifiedEvent)
def handleRepositoryModifiedEvent(item, event):
    """
    Reconfigures the database when a repository is modified.
    """
    for description in event.descriptions:
        if 'session' in description.attributes:
            _configureRepositoryDataStore(item)


def _configureRepositoryDataStore(repository):
    """
    Helper method to install DataStore tables for a Repository
    """
    datastore = IDataStore(repository)
    session = datastore.session
    url = session.bind.url
    repository_name = repository.getId()
    session_name = repository.session
    msg_params = dict(repository=repository_name, session=session_name, url=url)

    log.info(MSG_INSALLING % msg_params)
    migrate.install(datastore.session.bind)


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
