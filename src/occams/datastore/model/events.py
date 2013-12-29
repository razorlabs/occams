from sqlalchemy import event

from occams.datastore.model.metadata import updateMetadata, Modifiable
from occams.datastore.model.auditing import createRevision, Auditable
from occams.datastore.model.schema import setChecksum, Attribute
from occams.datastore.model.storage import Entity, enforceSchemaState


def onBeforeFlush(session, flush_context, instances):
    """
    Handles the ``before_flush`` event of DataStore's custom session
    """
    for instance in iter(session.new):
        dispatch(instance, 'new')
    for instance in iter(session.dirty):
        dispatch(instance, 'dirty')
    for instance in iter(session.deleted):
        dispatch(instance, 'deleted')


def dispatch(instance, state):
    """
    Dispatches the events to the instances
    """

    if isinstance(instance, Attribute) and state in ('new', 'dirty'):
        setChecksum(instance)

    if isinstance(instance, Entity) and state in ('new', 'dirty'):
        enforceSchemaState(instance)

    if isinstance(instance, Modifiable) and state in ('new', 'dirty'):
        updateMetadata(instance, created=(state == 'new'))

    if isinstance(instance, Auditable) and state in ('dirty'):
        createRevision(instance, deleted=False)

    if isinstance(instance, Auditable) and state in ('deleted'):
        # Audit the last revision of the row
        createRevision(instance, deleted=True)
        # If the row keeps track of its metadata, we want to record who deleted
        # the row as well, so issue a final touch and then audit again
        if isinstance(instance, Modifiable):
            updateMetadata(instance, created=False)
            createRevision(instance, deleted=True)


def register(session):
    """
    Registers event listeners.
    """
    event.listen(session, 'before_flush', onBeforeFlush)
