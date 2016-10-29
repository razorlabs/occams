from pyramid.view import view_config

from .. import _, models


@view_config(
    route_name='forms.workflow',
    permission='view',
    renderer='../templates/workflow/view.pt')
def view(context, request):
    """
    Displays default workflow
    """

    dbsession = request.dbsession

    states = dbsession.query(models.State).order_by(models.State.name)

    return {
        'states': iter(states),
        'states_count': states.count(),
    }
