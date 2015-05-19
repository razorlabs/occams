from pyramid.httpexceptions import HTTPFound
from pyramid.security import forget
from pyramid.view import view_config
import wtforms
import wtforms.fields.html5

from occams import Session
from occams_datastore import models as datastore

from .. import _


class LoginForm(wtforms.Form):

    login = wtforms.fields.html5.EmailField(
        _(u'Login'),
        validators=[
            wtforms.validators.InputRequired(),
            wtforms.validators.Length(max=128)])

    password = wtforms.PasswordField(
        _(u'Password'),
        validators=[
            wtforms.validators.InputRequired(),
            wtforms.validators.Length(max=1024)])


@view_config(route_name='accounts.login', renderer='../templates/login.pt')
def login(request):

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
            request.session.flash(_(u'Invalid credentials'), 'danger')
        else:
            user = (
                Session.query(datastore.User)
                .filter_by(key=form.login.data)
                .first())
            if not user:
                user = datastore.User(key=form.login.data)
                Session.add(user)

            referrer = request.GET.get('referrer')
            if not referrer or request.route_path('accounts.login') in referrer:
                # TODO: Maybe send the user to their user dashboard instead?
                referrer = request.route_path('occams.main')

            return HTTPFound(location=referrer, headers=headers)

    # forcefully forget any credentials
    request.response.headerlist.extend(forget(request))

    return {'form': form}
