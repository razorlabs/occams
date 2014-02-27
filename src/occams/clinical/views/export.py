from collections import defaultdict
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
from sqlalchemy import orm, null
import transaction

from occams.clinical import _, models, Session
from occams.clinical.celery import app
from occams.clinical.celery.export import make_export
from occams.clinical.widgets.pager import Pager


@view_config(
    route_name='export_home',
    permission='fia_view',
    renderer='occams.clinical:templates/export/about.pt')
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


def existent_schema_validator(value):
    """
    Deferred validator to determine the schema choices at request-time.
    """
    if not value:
        return _(u'No schemata specified')
    names_query = (
        Session.query(models.Schema.name)
        .filter(models.Schema.publish_date != null())
        .filter(models.Schema.retract_date == null())
        .filter(models.Schema.name.in_(value)))
    names = set([name for name, in names_query])
    value = set(value)
    if names != value:
        return _(u'Invalid schemata chosen')
    return True


@colander.deferred
def limit_validator(node, kw):
    request = kw['request']

    def validator(schema, value):
        limit = request.registry.settings.get('app.export.limit')
        if not limit:
            return
        exports_query = query_exports(request)
        exports_count = exports_query.count()
        if exports_count >= int(limit):
            raise colander.Invalid(schema, _(u'Export limit exceeded'))
    return validator


class ExportCheckoutSchema(CSRFSchema):
    """
    Export checkout serialization schema
    """

    @colander.instantiate(
        validator=colander.Function(existent_schema_validator))
    class schemata(colander.SequenceSchema):

        name = colander.SchemaNode(colander.String())

    expand_collections = colander.SchemaNode(
        colander.Boolean())

    use_choice_labels = colander.SchemaNode(
        colander.Boolean())


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
    errors = {}
    cstruct = {
        # Organize inputs since we're manually rendering forms
        'schemata': request.POST.getall('schemata'),
        'csrf_token': request.POST.get('csrf_token'),
        'expand_collections': request.POST.get('expand_collections', 'false'),
        'use_choice_labels': request.POST.get('use_choice_labels', 'false')}
    form = (
        ExportCheckoutSchema(validator=limit_validator)
        .bind(request=request))

    if request.method == 'POST':
        try:
            appstruct = form.deserialize(cstruct)
        except colander.Invalid as e:
            errors = e.asdict()
        else:
            export = models.Export(
                expand_collections=appstruct['expand_collections'],
                use_choice_labels=appstruct['use_choice_labels'],
                name=str(uuid.uuid4()),
                owner_user=(
                    Session.query(models.User)
                    .filter_by(key=request.authenticated_userid)
                    .one()),
                schemata=(
                    Session.query(models.Schema)
                    .filter(models.Schema.name.in_(appstruct['schemata']))
                    .filter(models.Schema.publish_date != null())
                    .filter(models.Schema.retract_date == null())
                    .all()))
            Session.add(export)
            Session.flush()
            task_id = export.name
            task = make_export.subtask(args=(export.id,))
            # Avoid race-conditions by executing the task after
            # the current request completes successfully
            transaction.get().addAfterCommitHook(
                lambda success: success and task.apply_async(task_id=task_id))
            request.session.flash(
                _(u'Your request has been received!'), 'success')
            return HTTPFound(location=request.route_path('export_status'))

    layout = request.layout_manager.layout
    layout.title = _(u'Exports')
    layout.set_nav('export_nav')

    limit = request.registry.settings.get('app.export.limit')
    exceeded = False

    if limit:
        exports_count = query_exports(request).count()
        if exports_count >= int(limit):
            exceeded = True
            request.session.flash(
                _(u'You have exceed your export limit of ${limit}',
                    mapping={'limit': limit}),
                'warning')

    schemata_query = query_schemata()
    versions = get_versions()

    return {
        'exceeded': exceeded,
        'errors': errors,
        'cstruct': cstruct,
        'schemata': schemata_query,
        'versions': versions,
        'schemata_count': schemata_query.count()}


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
def status_json(request):
    """
    Returns the current exports statuses.
    """

    exports_query = query_exports(request)
    exports_count = exports_query.count()
    versions = get_versions()
    export_dir = request.registry.settings['app.export.dir']

    pager = Pager(request.GET.get('page', 1), 5, exports_count)
    exports_query = exports_query[pager.slice_start:pager.slice_end]

    localizer = get_localizer(request)
    locale = negotiate_locale_name(request)

    result = {
        'csrf_token': request.session.get_csrf_token(),
        'pager': pager.serialize(),
        'exports': []
    }

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
            return format_datetime(export.create_date + delta, locale=locale)

    for export in exports_query:
        count = len(export.schemata)
        serialized = {
            'id': export.id,
            'name': export.name,
            'title': localizer.pluralize(
                _(u'Export containing ${count} item'),
                _(u'Export containing ${count} items'),
                count, 'occams.clinical', mapping={'count': count}),
            'status': export.status,
            'count': None,
            'total': None,
            'file_size': file_size(export),
            'download_url': request.route_path('export_download',
                                               id=export.id),
            'delete_url': request.route_path('export_delete', id=export.id),
            'create_date': format_datetime(export.create_date, locale=locale),
            'expire_date': expire_date(export),
            'items': []
            }
        for schema in query_schemata([s.id for s in export.schemata]):
            serialized['items'].append({
                'name': schema.name,
                'title': schema.title,
                'has_private': schema.has_private,
                'versions': list(map(str, versions[schema.name])),
                })
        result['exports'].append(serialized)
    return result


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

    app.control.revoke(export.name)

    return HTTPOk()


@view_config(
    route_name='export_download',
    permission='fia_view')
def download(request):
    """
    Returns specific download attachement

    The user should only be allowed to download their exports.
    """
    userid = request.authenticated_userid

    try:
        export = (
            Session.query(models.Export)
            .filter_by(id=request.matchdict['id'], status='complete')
            .filter(models.Export.owner_user.has(key=userid))
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

    exports_query = (
        Session.query(models.Export)
        .filter(models.Export.owner_user.has(key=userid)))

    if export_expire:
        cutoff = datetime.now() - timedelta(int(export_expire))
        exports_query = (
            exports_query.filter(models.Export.create_date >= cutoff))

    exports_query = (
        exports_query.order_by(models.Export.create_date.desc()))

    return exports_query


def query_schemata(ids=None):
    """
    Helper function to fetch schemata summary
    """

    InnerSchema = orm.aliased(models.Schema)
    OuterSchema = orm.aliased(models.Schema)
    schemata_query = (
        Session.query(OuterSchema.name)
        .add_column(
            Session.query(
                Session.query(models.Attribute)
                .filter(models.Attribute.is_private)
                .join(InnerSchema)
                .filter(InnerSchema.name == OuterSchema.name)
                .correlate(OuterSchema)
                .exists())
            .as_scalar()
            .label('has_private'))
        .add_column(
            Session.query(InnerSchema.title)
            .select_from(InnerSchema)
            .filter(InnerSchema.name == OuterSchema.name)
            .filter(InnerSchema.publish_date != null())
            .filter(InnerSchema.retract_date == null())
            .order_by(InnerSchema.publish_date.desc())
            .limit(1)
            .correlate(OuterSchema)
            .as_scalar()
            .label('title'))
        .filter(OuterSchema.publish_date != null())
        .filter(OuterSchema.retract_date == null())
        .filter(
            # Do not include forms that are used for randomization
            ~Session.query(models.Entity.schema_id)
            .join(models.Entity.contexts)
            .filter(models.Context.external == 'stratum')
            .join(models.Stratum, models.Context.key == models.Stratum.id)
            .filter(models.Entity.schema_id == OuterSchema.id)
            .correlate(OuterSchema)
            .exists()))

    if ids:
        schemata_query = (
            schemata_query
            .filter(OuterSchema.id.in_(ids)))

    schemata_query = (
        schemata_query
        .group_by(OuterSchema.name)
        .order_by('title'))

    return schemata_query


def get_versions():
    """
    Helper function to build a dictionary of all schemata's versions
    """
    version_query = (
        Session.query(models.Schema.name, models.Schema.publish_date)
        .filter(models.Schema.publish_date != null())
        .filter(models.Schema.retract_date == null())
        .order_by(
            models.Schema.name.asc(),
            models.Schema.publish_date.desc()))

    versions = defaultdict(list)

    for name, publish_date in version_query:
        versions[name].append(publish_date)

    return versions
