import colander
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from sqlalchemy import orm
import transaction

from occams.datastore import model as datastore

from .. import _, log, models, Session


@view_config(
    route_name='site_list',
    permission='site_view',
    renderer='occams.clinical:templates/site/list.pt')
def list_(request):
    request.layout_manager.layout.content_title = _(u'Sites')
    sites_query = (
        Session.query(models.Site)
        .order_by(models.Site.title.asc()))
    return {
        'sites': sites_query,
        'sites_count': sites_query.count()}




