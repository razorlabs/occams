from pyramid.view import view_config

from occams.datastore import models
from .. import Session


@view_config(
    route_name='workflow',
    permission='view',
    renderer='../templates/workflow/view.pt')
def view(context, request):
    """
    Displays default workflow
    """

    states = Session.query(models.State).order_by(models.State.name)

    return {
        'states': iter(states),
        'states_count': states.count(),
    }
