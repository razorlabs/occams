from good import *   # NOQA
from pyramid.httpexceptions import HTTPFound, HTTPForbidden
from pyramid.security import forget
from pyramid.view import view_config, forbidden_view_config

from .. import _, Session, models
from ..validators import String


@forbidden_view_config()
def forbidden(request):
    if (request.matched_route.name != 'login'
            and request.authenticated_userid):
        # If an authenticated user has reached this controller without
        # intentionally going to the login view, assume permissions
        # error
        return HTTPForbidden(_(u'Permission denied'))

    return HTTPFound(location=request.route_path('login', _query={
        'referrer': request.current_route_path()
        }))


@view_config(
    route_name='login',
    renderer='../templates/auth/login.pt')
def login(request):

    if request.authenticated_userid:
        return HTTPFound(location=request.route_path('forms'))

    error = None
    data = None

    schema = Schema({
        'login': All(String(), Length(max=32)),
        'password': All(String(), Length(max=128))
        })

    referrer = request.GET.get('referrer') or request.current_route_path()

    # Only process the input if the user intented to post to this view
    # (could be not-logged-in redirect)
    if request.method == 'POST' and request.matched_route.name == 'login':
        try:
            data = schema(request.POST.mixed())
        except Invalid:
            error = _(u'Invalid input')
        else:
            # XXX: Hack for this to work on systems that have not set the
            # environ yet. Pyramid doesn't give us access to the policy
            # publicly, put it's still available throught this private
            # variable and it's usefule in leveraging repoze.who's
            # login mechanisms...
            who_api = request._get_authentication_policy()._getAPI(request)

            authenticated, headers = who_api.login(data)

            if not authenticated:
                error = _(u'Invalid credentials')
            else:
                user = (
                    Session.query(models.User)
                    .filter_by(key=data['login'])
                    .first())
                if not user:
                    Session.add(models.User(key=request.login.data))
                return HTTPFound(location=referrer, headers=headers)

    # forcefully forget any credentials
    request.response_headerlist = forget(request)

    return {
        'data': data,
        'error': error,
        'referrer': referrer
    }


@view_config(route_name='logout')
def logout(request):
    return HTTPFound(location='/', headers=forget(request))
