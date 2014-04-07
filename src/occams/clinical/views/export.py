from datetime import datetime, timedelta
import os
import uuid

from babel.dates import format_datetime
import colander
import humanize
from pyramid_deform import CSRFSchema
from pyramid.i18n import get_localizer, negotiate_locale_name
from pyramid.httpexceptions import HTTPFound, HTTPNotFound, HTTPOk
from pyramid.response import FileResponse
from pyramid.view import view_config
import six
from sqlalchemy import orm
import transaction

from .. import _, models, Session, exports
from ..tasks import celery,  make_export
from ..widgets.pager import Pager


@view_config(
    route_name='export_home',
    permission='fia_view',
    renderer='occams.clinical:templates/export/home.pt')
def about(request):
    """
    General intro-page so users know what they're getting into.
    """
    layout = request.layout_manager.layout
    layout.title = _(u'Exports')
    layout.set_nav('export_nav')
    return {}


@view_config(
    route_name='export_faq',
    permission='fia_view',
    renderer='occams.clinical:templates/export/faq.pt')
def faq(request):
    """
    Verbose details about how this tool works.
    """
    layout = request.layout_manager.layout
    layout.title = _(u'Exports')
    layout.set_nav('export_nav')
    return {}


@colander.deferred
def contents_validator(node, kw):
    """
    Deferred validator to determine the schema choices at request-time.
    """
    return colander.All(
        colander.Length(min=1),
        colander.ContainsOnly(kw['allowed_names']), )


@colander.deferred
def schema_validator(node, kw):
    def validator(schema, value):
        if kw['limit_exceeded']:
            raise colander.Invalid(schema, _(u'Export limit exceeded'))
    return validator


class ExportCheckoutSchema(CSRFSchema):
    """
    Export checkout serialization schema
    """

    contents = colander.SchemaNode(
        colander.Set(),
        # Currently does nothing as colander 1.0b1 is hard-coded to "Required"
        missing_msg=_(u'Please select an item'),
        validator=contents_validator)

    expand_collections = colander.SchemaNode(
        colander.Boolean(),
        default=False)

    use_choice_labels = colander.SchemaNode(
        colander.Boolean(),
        default=False)


@view_config(
    route_name='export_add',
    permission='fia_view',
    renderer='occams.clinical:templates/export/add.pt')
def add(request):
    """
    Generating a listing of available data for export.

    Because the exports can take a while to generate, this view serves
    as a "checkout" page so that the user can select which files they want.
    The actual exporting process is then queued in a another thread so the user
    isn't left with an unresponsive page.
    """
    layout = request.layout_manager.layout
    layout.title = _(u'Exports')
    layout.set_nav('export_nav')

    errors = None
    cstruct = None
    exportables = exports.list_all(include_rand=False)
    limit = request.registry.settings.get('app.export.limit')
    exceeded = limit and query_exports(request).count() > limit

    cschema = ExportCheckoutSchema(validator=schema_validator).bind(
        request=request,
        limit_exceeded=exceeded,
        allowed_names=exportables.keys())

    if request.method == 'POST':
        try:
            cstruct = request.POST.mixed()
            # Force list of contents
            if isinstance(cstruct['contents'], six.string_types):
                cstruct['contents'] = set([cstruct['contents']])
            appstruct = cschema.deserialize(cstruct)
        except colander.Invalid as e:
            errors = e.asdict()
        else:
            task_id = six.u(str(uuid.uuid4()))
            Session.add(models.Export(
                name=task_id,
                expand_collections=appstruct['expand_collections'],
                use_choice_labels=appstruct['use_choice_labels'],
                owner_user=(Session.query(models.User)
                            .filter_by(key=request.authenticated_userid)
                            .one()),
                contents=[exportables[k].to_json()
                          for k in appstruct['contents']]))

            def apply_after_commit(success):
                if success:
                    make_export.apply_async(args=[task_id], task_id=task_id)

            # Avoid race-condition by executing the task after succesful commit
            transaction.get().addAfterCommitHook(apply_after_commit)

            msg = _(u'Your request has been received!')
            request.session.flash(msg, 'success')

            return HTTPFound(location=request.route_path('export_status'))

    return {
        'cstruct': cstruct or cschema.serialize(),
        'exceeded': exceeded,
        'errors': errors,
        'limit': limit,
        'exportables': exportables,
        'schemata_count': len(exportables)}


@view_config(
    route_name='export_status',
    permission='fia_view',
    renderer='occams.clinical:templates/export/status.pt')
def status(request):
    """
    Renders the view that will contain progress of exports.

    All exports will be loaded asynchronously via seperate ajax call.
    """
    layout = request.layout_manager.layout
    layout.title = _(u'Exports')
    layout.set_nav('export_nav')
    return {}


@view_config(
    route_name='export_status',
    permission='fia_view',
    xhr=True,
    renderer='json')
@view_config(
    # For quick debbuging
    route_name='export_status',
    permission='fia_view',
    request_param='xhr',
    renderer='json')
def status_json(request):
    """
    Returns the current exports statuses.
    """

    exports_query = query_exports(request)
    exports_count = exports_query.count()
    export_dir = request.registry.settings['app.export.dir']

    pager = Pager(request.GET.get('page', 1), 5, exports_count)
    exports_query = exports_query[pager.slice_start:pager.slice_end]

    locale = negotiate_locale_name(request)
    localizer = get_localizer(request)

    try:
        delta = timedelta(request.registry.settings.get('app.export.expire'))
    except ValueError:
        delta = None

    def file_size(export):
        if export.status == 'complete':
            path = os.path.join(export_dir, export.name)
            return humanize.naturalsize(os.path.getsize(path))

    def expire_date(export):
        if delta:
            return format_datetime(export.modify_date + delta, locale=locale)

    def export2json(export):
        count = len(export.contents)
        return {
            'id': export.id,
            'title': localizer.pluralize(
                _(u'Export containing ${count} item'),
                _(u'Export containing ${count} items'),
                count, 'occams.clinical', mapping={'count': count}),
            'name': export.name,
            'status': export.status,
            'use_choice_labels': export.use_choice_labels,
            'expand_collections': export.expand_collections,
            'contents': sorted(export.contents, key=lambda v: v['title']),
            'count': None,
            'total': None,
            'file_size': file_size(export),
            'download_url': request.route_path('export_download',
                                               id=export.id),
            'delete_url': request.route_path('export_delete', id=export.id),
            'create_date': format_datetime(export.create_date, locale=locale),
            'expire_date': expire_date(export)}

    return {
        'csrf_token': request.session.get_csrf_token(),
        'pager': pager.serialize(),
        'exports': list(map(export2json, exports_query))}


@view_config(
    route_name='export_delete',
    permission='fia_view',
    request_method='POST',
    xhr=True
    )
def delete(request):
    """
    Handles delete delete AJAX request
    """
    export = Session.query(models.Export).get(request.matchdict['id'])
    csrf_token = request.POST.get('csrf_token')

    if not export or csrf_token != request.session.get_csrf_token():
        raise HTTPNotFound

    Session.delete(export)
    Session.flush()

    celery.control.revoke(export.name)

    return HTTPOk()


@view_config(
    route_name='export_download',
    permission='fia_view')
def download(request):
    """
    Returns specific download attachement

    The user should only be allowed to download their exports.
    """
    try:
        export = (
            Session.query(models.Export)
            .filter_by(id=request.matchdict['id'], status='complete')
            .filter(models.Export.owner_user.has(
                key=request.authenticated_userid))
            .one())
    except orm.exc.NoResultFound:
        raise HTTPNotFound

    export_dir = request.registry.settings['app.export.dir']
    path = os.path.join(export_dir, export.name)

    response = FileResponse(path)
    response.content_disposition = 'attachment;filename=export.zip'
    return response


def query_exports(request):
    """
    Helper method to query current exports for the authenticated user
    """
    userid = request.authenticated_userid
    export_expire = request.registry.settings.get('app.export.expire')

    query = (
        Session.query(models.Export)
        .filter(models.Export.owner_user.has(key=userid)))

    if export_expire:
        cutoff = datetime.now() - timedelta(int(export_expire))
        query = query.filter(models.Export.modify_date >= cutoff)

    query = query.order_by(models.Export.create_date.desc())

    return query
