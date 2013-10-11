import colander
import deform
from pyramid_deform import CSRFSchema
from pyramid.httpexceptions import HTTPFound
from pyramid.response import FileIter
from pyramid.view import view_config
from sqlalchemy import func, orm, sql
import transaction

from occams.datastore import model as datastore

from .. import _, log, models, Session, tasks


@colander.deferred
def deferred_ecrf_validator(node, kw):
    """
    Deferred validator to determine the ecrf choices at runtime.
    """
    ids_query = (
        Session.query(datastore.Schema.id)
        .filter(datastore.Schema.publish_date != None))
    valid_ids = set([r.id for r in ids_query])
    return colander.OneOf(valid_ids)


class ExportCheckoutSchema(CSRFSchema):
    """
    Export checkout serialization schema
    """

    @colander.instantiate()
    class tables(colander.SequenceSchema):

        name = colander.SchemaNode(
            colander.String(),
            validator=colander.OneOf(models.BUILTINS.keys()))

    @colander.instantiate()
    class ecrfs(colander.SequenceSchema):

        id = colander.SchemaNode(
            colander.Int(),
            validator=deferred_ecrf_validator)

    def validator(self, node, cstruct):
        if not(cstruct['tables'] or cstruct['ecrfs']):
           raise colander.Invalid(node, _(u'No values selected.'))


@view_config(
    route_name='data_list',
    permission='fia_view',
    renderer='occams.clinical:templates/data/list.pt')
def list_(request):
    """
    List data that is available for download

    Becuase the exports can take a while to generate, this view serves
    as a "checkout" page so that the user can select which files they want.
    The actual exporting process is then queued in a another thread so the user
    isn't left with an unresponsive page.
    """

    if 'submit' in request.POST:
        schema = ExportCheckoutSchema().bind(request=request)
        # since we render the form manually, we gotta do this
        cstruct = {
            'csrf_token': request.POST.get('csrf_token'),
            'tables': request.POST.getall('tables'),
            'ecrfs': request.POST.getall('ecrfs')}
        form = deform.Form(schema)
        try:
            appstruct = form.validate(cstruct.items())
        except deform.exception.ValidationFailure as e:
            for error in e.error.asdict().values():
                request.session.flash(error, 'error')
        else:
            ### TODO: create archive file blob entry
            tasks.export.delay(request.user, appstruct['tables'], appstruct['ecrfs'])
            request.session.flash(_(u'Your request has been received and will be processed'), 'success')
            return HTTPFound(location=request.route_path('data_download'))

    layout = request.layout_manager.layout
    layout.title = _(u'Data')
    layout.set_nav('data_nav')

    ecrfs_query = (
        Session.query(datastore.Schema)
        .filter(datastore.Schema.publish_date != None)
        .order_by(
            datastore.Schema.name.asc(),
            datastore.Schema.publish_date.desc()))

    ecrfs_count = ecrfs_query.count()

    return {
        'csrf_token': request.session.get_csrf_token(),
        'builtins': sorted(models.BUILTINS.keys()),
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

    if 'id' not in request.GET:
        return {
            'duration': '1 week',
            'exports': exports,
            'has_exports': len(exports)}

    response = request.response
    response.app_iter = FileIter(attachment_fp)
    response.content_disposition = 'attachment;filename=clinical.zip'
    return response

