
from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config

from occams.datastore import models
from .. import Session


@view_config(
    route_name='workflow_view',
    renderer='occams.forms:templates/workflow/view.pt',
    permission='form_view')
def view(request):
    """
    Displya default workflow
    """
    name = request.matchdict['workflow']

    # Only support default for now
    if name != 'default':
        raise HTTPNotFound

    states = Session.query(models.State).order_by(models.State.name)

    return {
        'states': iter(states),
        'states_count': states.count(),
    }
