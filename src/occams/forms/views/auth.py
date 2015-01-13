from pyramid.httpexceptions import HTTPFound, HTTPForbidden
from pyramid.security import forget
from pyramid.view import view_config, forbidden_view_config
import wtforms

from .. import _, Session, models


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


class LoginForm(wtforms.Form):

    login = wtforms.StringField(
        _(u'Login'),
        validators=[
            wtforms.validators.InputRequired(),
            wtforms.validators.Length(max=32)])

    password = wtforms.PasswordField(
        _(u'Password'),
        validators=[
            wtforms.validators.InputRequired(),
            wtforms.validators.Length(max=128)])


@view_config(
    route_name='login',
    renderer='../templates/auth/login.pt')
def login(request):

    if request.authenticated_userid:
        return HTTPFound(location=request.route_path('forms'))

    error = None

    referrer = request.GET.get('referrer') or request.current_route_path()

    form = LoginForm(request.POST)

    if request.method == 'POST' and form.validate():
        # XXX: Hack for this to work on systems that have not set the
        # environ yet. Pyramid doesn't give us access to the policy
        # publicly, put it's still available throught this private
        # variable and it's usefule in leveraging repoze.who's
        # login mechanisms...
        who_api = request._get_authentication_policy()._getAPI(request)

        authenticated, headers = who_api.login(form.data)

        if not authenticated:
            error = _(u'Invalid credentials')
        else:
            user = (
                Session.query(models.User)
                .filter_by(key=form.login.data)
                .first())
            if not user:
                Session.add(models.User(key=request.login.data))
            return HTTPFound(location=referrer, headers=headers)

    # forcefully forget any credentials
    request.response_headerlist = forget(request)

    return {
        'form': form,
        'error': error,
        'referrer': referrer
    }


@view_config(route_name='logout')
def logout(request):
    return HTTPFound(location='/', headers=forget(request))
