from good import *  # NOQA
from pyramid.view import view_config


@view_config(
    route_name='settings',
    permission='admin',
    renderer='../templates/settings/view.pt')
def view(context, request):
    return {}
