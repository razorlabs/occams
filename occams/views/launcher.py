from pyramid.view import view_config


@view_config(
    route_name='occams.index',
    permission='view',
    renderer='../templates/launcher/index.pt'
    )
def index(context, request):
    """
    Renders all available applciations
    """
    return {}
