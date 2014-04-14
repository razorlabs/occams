import colander
import deform.widget
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config, forbidden_view_config

from .. import _, Session, models


class LoginSchema(colander.MappingSchema):

    login = colander.SchemaNode(
        colander.String(),
        title=None,
        validator=colander.All(
            colander.Email(),
            colander.Length(max=32)),
        widget=deform.widget.TextInputWidget(
            autofocus=True,
            placeholder=_(u'Email')))

    password = colander.SchemaNode(
        colander.String(),
        title=None,
        validator=colander.Length(min=5, max=32),
        widget=deform.widget.PasswordWidget(
            placeholder=_(u'Password')))


@view_config(
    route_name='account_login',
    renderer='occams.studies:templates/account/login.pt')
@forbidden_view_config(
    renderer='occams.studies:templates/account/login.pt')
def login(request):
    request.layout_manager.layout.title = _('Log In')
    request.layout_manager.layout.show_header = False

    # Figure out where the user came from so we can redirect afterwards
    referrer = request.GET.get('referrer', request.current_route_path())
    if not referrer or referrer == request.route_path('account_login'):
        # Never use the login as the referrer
        referrer = request.route_path('studies')

    form = deform.Form(
        schema=LoginSchema(title=_(u'Please log in')).bind(request=request),
        css_class='form-login',
        action=request.route_path(
            'account_login',
            _query={'referrer': referrer}),
        buttons=[
            deform.Button(
                'submit',
                title=_(u'Sign In'),
                css_class='btn btn-lg btn-primary btn-block')])

    # XXX: Hack for this to work on systems that have not set the
    # environ yet. Pyramid doesn't give us access to the policy publicly,
    # put it's still available throught this private variable and
    # it's usefule in leveraging repoze.who's login mechanisms...
    who_api = request._get_authentication_policy()._getAPI(request)

    if request.method == 'POST':
        try:
            appstruct = form.validate(request.POST.items())
        except deform.ValidationFailure as e:
            form = e
        else:
            authenticated, headers = who_api.login({
                'login': appstruct['login'],
                'password': appstruct['password']})
            if not authenticated:
                request.session.flash(_(u'Invalid credentials'), 'error')
            else:
                user = (
                    Session.query(models.User)
                    .filter_by(key=appstruct['login'])
                    .first())
                if not user:
                    Session.add(models.User(key=appstruct['login']))
                return HTTPFound(location=referrer, headers=headers)
    else:
        # Forcefully forget any existing credentials.
        __, headers = who_api.login({})

    # clear any authenticated user for the current request.
    request.response_headerlist = headers
    if 'REMOTE_USER' in request.environ:
        del request.environ['REMOTE_USER']

    return {'form': form.render()}


@view_config(route_name='account_logout')
def logout(request):
    who_api = request._get_authentication_policy()._getAPI(request)
    headers = who_api.forget()
    return HTTPFound(location=request.route_path('studies'), headers=headers)
