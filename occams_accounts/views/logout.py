from pyramid.httpexceptions import HTTPFound
from pyramid.security import forget
from pyramid.view import view_config

from .. import _


@view_config(route_name='logout')
def logout(request):
    login_url = request.route_path('login')
    forgotten_headers = forget(request)
    msg = _('You have been successfully logged out')
    request.session.invalidate()  # Clear all data
    request.session.flash(msg, 'success', allow_duplicate=False)
    return HTTPFound(location=login_url, headers=forgotten_headers)
