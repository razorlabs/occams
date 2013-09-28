import colander
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from sqlalchemy import func, orm, sql
import transaction

from occams.datastore import model as datastore

from .. import _, log, models, Session


@view_config(
    route_name='visit_list',
    permission='visit_view',
    renderer='occams.clinical:templates/visit/list.pt')
def list_(request):
    layout = request.layout_manager.layout
    layout.title = _(u'Welcome to OCCAMS!')
    return {}




