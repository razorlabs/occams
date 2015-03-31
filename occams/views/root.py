from pyramid.view import view_config


@view_config(
    route_name='occams',
    permission='view',
    renderer='../templates/root.pt')
def root(context, request):
    return {}
