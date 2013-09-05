import colander
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from sqlalchemy import orm
import transaction

from occams.datastore import model as datastore

from .. import _, log, Session


@view_config(
    route_name='home',
    permission='view',
    renderer='occams.clinical:templates/patient/search.pt')
def home(request):
    request.layout_manager.layout.content_title = _(u'Welcome')
    return {}




