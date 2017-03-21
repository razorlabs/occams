from pyramid.httpexceptions import HTTPFound
from pyramid.security import forget
from pyramid.view import view_config
import wtforms
import wtforms.fields.html5

from .. import _, models


class LoginForm(wtforms.Form):

    # Doesn't actually validate email input, just generates the
    #  <input type="email" field. So we still need to do a bit of
    # input validation in case input is from other sources such as a
    # curl script
    login = wtforms.fields.html5.EmailField(
        _(u'Login'),
        validators=[
            wtforms.validators.InputRequired(message='Account email required'),
            # Emails can only be 254 characters long:
            #   http://stackoverflow.com/a/1199238
            wtforms.validators.Length(
                min=10, max=254, message='Invalid email length'),
            # Validate 99.99% of acceptable email formats
            wtforms.validators.Regexp(
                r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)',
                message='Invalid email format'
            ),
        ])

    password = wtforms.PasswordField(
        _(u'Password'),
        validators=[
            wtforms.validators.InputRequired(message='Password required'),
            # Enforce a limit on password lengh input to prevent
            # submissions of excessively long paragraphs
            # https://www.owasp.org/index.php/Authentication_Cheat_Sheet
            wtforms.validators.Length(
                max=128, message='Invalid password length')
        ])


@view_config(route_name='accounts.login', renderer='../templates/login.pt')
def login(request):

    dbsession = request.dbsession
    form = LoginForm(request.POST)
    errors = []

    if request.method == 'POST' and form.validate():
        # XXX: Hack for this to work on systems that have not set the
        # environ yet. Pyramid doesn't give us access to the policy
        # publicly, put it's still available throught this private
        # variable and it's usefule in leveraging repoze.who's
        # login mechanisms...
        who_api = request._get_authentication_policy()._getAPI(request)

        authenticated, headers = who_api.login(form.data)

        if not authenticated:
            errors += [_(u'Invalid credentials')]
        else:
            referrer = request.GET.get('referrer')
            if not referrer or request.route_path('accounts.login') in referrer:
                # TODO: Maybe send the user to their user dashboard instead?
                referrer = request.route_path('occams.index')

            return HTTPFound(location=referrer, headers=headers)

    # forcefully forget any credentials
    request.response.headerlist.extend(forget(request))

    return {
        'form': form,
        'errors': errors + list(form.login.errors) + list(form.password.errors)
    }
