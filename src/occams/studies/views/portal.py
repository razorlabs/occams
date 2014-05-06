import colander
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from sqlalchemy import func, orm, sql

from .. import _, log, models, Session


@view_config(
    route_name='home',
    permission='view',
    renderer='occams.studies:templates/portal/home.pt')
def home(request):
    return {}
