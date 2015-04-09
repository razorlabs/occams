from pyramid.view import view_config


@view_config(
    route_name='occams.main',
    permission='view',
    renderer='../templates/root.pt')
def root(context, request):
    """
    Renders all available applciations
    """
    return {}
