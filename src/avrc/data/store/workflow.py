""" 
Very basic workflow support for EAV entities.
"""

from avrc.data.store import model

def setup_states(datastore, states, default):
    """ 
    Updates the possible states for DataStore entities
    """
    session = datastore.session

    # Remove any old states

    query = (
        session.query(model.State)
        .filter(~model.State.name.in_([term.token for term in list(states)]))
        )

    query.delete('fetch')

    # Add new states

    for term in list(states):
        name = term.token
        title = term.title and term.title or unicode(name)

        if 0 >= session.query(model.State).filter_by(name=name).count():
            session.add(model.State(name=name, title=title))

    # Update the default

    result = (
        session.query(model.State)
        .filter(model.State.name == default)
        .update(dict(is_default=True), 'fetch')
        )

    result = (
        session.query(model.State)
        .filter(model.State.name != default)
        .update(dict(is_default=False), 'fetch')
        )

    session.flush()
