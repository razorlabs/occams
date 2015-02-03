from pyramid.view import view_config


@view_config(
    route_name='account',
    permission='view',
    renderer='../templates/account/view.pt')
def view(context, request):
    return {}
