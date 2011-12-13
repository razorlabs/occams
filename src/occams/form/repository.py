"""
Repository tools
"""

from zope.component import getUtilitiesFor
from zope.component import adapter
from zope.interface import implementer
from zope.interface import implements
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.vocabulary import SimpleTerm

from z3c.saconfig import named_scoped_session
from z3c.saconfig.interfaces import IScopedSession

from avrc.data.store import model
from avrc.data.store.upgrades import migrate
from avrc.data.store.interfaces import IDataStore

from occams.form import MessageFactory as _
from occams.form import Logger as log
from occams.form.interfaces import IRepository


MSG_INSALLING = _(u'Configuring "%(repository)s" at "%(url)s" (%(session)s)')


class AvailableSessionsVocabularyFactory(object):
    """
    Builds a vocabulary containing the Plone instance's registered 
    ``z3c.saconfig`` sessions.
    """
    implements(IVocabularyFactory)

    def __call__(self, context):
        registered = getUtilitiesFor(IScopedSession)
        names = [name for name, utility in registered]
        return SimpleVocabulary.fromValues(names)


class RepositoryFormsVocabularyFactory(object):
    """
    Builds a vocabulary containing all the form names in the context
    """
    implements(IVocabularyFactory)

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


@adapter(IRepository)
@implementer(IScopedSession)
def getRespositorySession(context):
    """
    Retrieves the session specified by the repository
    """
    return named_scoped_session(context.session)


@adapter(IRepository)
@implementer(IDataStore)
def getRespositoryDataStore(context):
    """
    Retrieves the a datastore using the session specified by the repository
    """
    return IDataStore(named_scoped_session(context.session))


def handleRepositoryAddedEvent(item, event):
    """
    Sets up the database when a repository is created.
    """
    _configureRepositoryDataStore(item)


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
