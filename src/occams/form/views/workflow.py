from datetime import date

from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config
from sqlalchemy import func, orm, sql, null, cast, Unicode
from wtforms import StringField, validators, ValidationError

from occams.datastore.utils.sql import group_concat
from occams.datastore import models
from occams.form import _, Session
from occams.form.csrf import CsrfForm


@view_config(
    route_name='workflow_view',
    renderer='occams.form:templates/workflow/view.pt',
    permission='form_view')
def view(request):
    """
    Displya default workflow
    """
    name = request.matchdict['workflow']

    # Only support default for now
    if name != 'default':
        raise HTTPNotFound

    states = Session.query(models.State).order_by(models.State.name)

    return {
        'states': iter(states),
        'states_count': states.count(),
    }
