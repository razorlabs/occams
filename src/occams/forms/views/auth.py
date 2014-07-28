from pyramid.httpexceptions import HTTPFound, HTTPForbidden
from pyramid.security import forget
from pyramid.view import view_config, forbidden_view_config
import wtforms
import wtforms.widgets.html5

from .. import _, Session, models


@view_config(
    route_name='login',
    renderer='../templates/auth/login.pt')
@forbidden_view_config(
    renderer='../templates/auth/login.pt')
def login(request):

    if (request.matched_route.name != 'login'
            and request.authenticated_userid):
        # If an authenticated user has reached this controller without
        # intentionally going to the login view, assume permissions
        # error
        return HTTPForbidden(_(u'Permission denied'))

    # Figure out where the user came from so we can redirect afterwards
    referrer = request.GET.get('referrer', request.current_route_path())

    if not referrer or referrer == request.route_path('login'):
        # Never use the login as the referrer
        referrer = request.route_path('home')

    form = LoginForm(request.POST)

    # Only process the input if the user intented to post to this view
    # (could be not-logged-in redirect)
    if (request.method == 'POST'
            and request.matched_route.name == 'login'
            and form.validate()):
        # XXX: Hack for this to work on systems that have not set the
        # environ yet. Pyramid doesn't give us access to the policy
        # publicly, put it's still available throught this private
        # variable and it's usefule in leveraging repoze.who's
        # login mechanisms...
        who_api = request._get_authentication_policy()._getAPI(request)

        authenticated, headers = who_api.login({
            'login': form.login.data,
            'password': form.password.data})
        if not authenticated:
            request.session.flash(_(u'Invalid credentials'), 'error')
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
        'referrer': referrer
    }


@view_config(route_name='logout')
def logout(request):
    return HTTPFound(location='/', headers=forget(request))


class LoginForm(wtforms.Form):

    login = wtforms.StringField(
        label=_(u'Email address'),
        widget=wtforms.widgets.html5.EmailInput(),
        validators=[
            wtforms.validators.required(),
            wtforms.validators.Length(max=32),
            wtforms.validators.Email(),
        ])

    password = wtforms.PasswordField(
        label=_(u'Password'),
        validators=[
            wtforms.validators.required(),
            wtforms.validators.Length(min=5, max=32)
        ])
