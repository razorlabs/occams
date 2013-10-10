from pyramid.response import FileIter
from pyramid.view import view_config
from sqlalchemy import func, orm, sql
import transaction

from occams.datastore import model as datastore

from .. import _, log, models, Session
from ..utils.iter import partition
from ..models import BUILTINS


@view_config(
    route_name='data_list',
    permission='fia_view',
    request_method='GET',
    renderer='occams.clinical:templates/data/list.pt')
def list_(request):
    """
    List data that is available for download

    Becuase the exports can take a while to generate, this view serves
    as a "checkout" page so that the user can select which files they want.
    The actual exporting process is handled in a another thread so the user
    isn't left with an unresponsive page load.
    """
    layout = request.layout_manager.layout
    layout.title = _(u'Data')
    layout.set_nav('data_nav')

    csrf = request.session.get_csrf_token()

    ecrfs_query = (
        Session.query(datastore.Schema)
        .filter(datastore.Schema.publish_date != None)
        .order_by(
            datastore.Schema.name.asc(),
            datastore.Schema.publish_date.desc()))

    ecrfs_count = ecrfs_query.count()

    return {
        'csrf': csrf,
        'builtins': sorted(BUILTINS.keys()),
        'ecrfs': ecrfs_query,
        'has_ecrfs': ecrfs_count > 0,
        'ecrfs_count': ecrfs_count}


@view_config(
    route_name='data_download',
    permission='fia_view',
    renderer='occams.clinical:templates/data/download.pt')
def download(request):
    """
    Lists current export jobs.

    This is where the user can view the progress of the exports and download them
    at a later time.
    """
    layout = request.layout_manager.layout
    layout.title = _(u'Data')
    layout.set_nav('data_nav')
    exports = []

    if 'id' in request.GET:
        response = request.response
        response.app_iter = FileIter(attachment_fp)
        response.content_disposition = 'attachment;filename=clinical.zip'
        return response

    return {
        'duration': '1 week',
        'exports': exports,
        'has_exports': len(exports)}

