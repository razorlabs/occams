from collections import namedtuple

from pyramid.httpexceptions import HTTPFound
from pyramid_layout.layout import layout_config
from pyramid_layout.panel import panel_config
from pyramid.view import view_config
from sqlalchemy import func, orm, sql
import transaction

from occams.datastore import model as datastore

from .. import _, log, models, Session


@view_config(
    route_name='data_list',
    permission='data_view',
    renderer='occams.clinical:templates/data/list.pt')
def list_(request):
    exports_query = (
        Session.query(datastore.Schema)
        .filter(datastore.Schema.publish_date != None)
        .order_by(
            datastore.Schema.name.asc(),
            datastore.Schema.publish_date.desc()))
    return {
        'exports': exports_query,
        'exports_count': exports_query.count()}
