from datetime import datetime, timedelta
import os.path

from babel.dates import format_timedelta
import colander
import deform
from pyramid_deform import CSRFSchema
from pyramid.i18n import negotiate_locale_name
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.response import FileResponse
from pyramid.security import authenticated_userid
from pyramid.view import view_config
from sqlalchemy import orm, null
import transaction

from occams.clinical import _, models, Session, tasks


def existent_schema_validator(value):
    """
    Deferred validator to determine the schema choices at request-time.
    """
    if not value:
        return _(u'No schemata specified')
    ids_query = (
        Session.query(models.Schema.id)
        .filter(models.Schema.publish_date != null())
        .filter(models.Schema.id.in_(value)))
    ids = set([id for id, in ids_query])
    value = set(value)
    if ids != value:
        return _(u'Invalid schemata chosen')
    return True


@colander.deferred
def limit_validator(node, kw):
    request = kw['request']

    def validator(schema, value):
        limit = request.registry.settings.get('app.export_limit')
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

        id = colander.SchemaNode(colander.Int())


@view_config(
    route_name='data_list',
    permission='fia_view',
    renderer='occams.clinical:templates/data/list.pt')
def list_(request):
    """
    List data that is available for download

    Because the exports can take a while to generate, this view serves
    as a "checkout" page so that the user can select which files they want.
    The actual exporting process is then queued in a another thread so the user
    isn't left with an unresponsive page.
    """
    form = deform.Form(
        ExportCheckoutSchema(validator=limit_validator).bind(request=request))

    if request.method == 'POST':
        try:
            appstruct = form.validate(request.POST.mixed().items())
        except deform.ValidationFailure as e:
            form = e
        else:
            export = models.Export(
                owner_user=(
                    Session.query(models.User)
                    .filter_by(key=authenticated_userid(request))
                    .one()),
                schemata=(
                    Session.query(models.Schema)
                    .filter(models.Schema.id.in_(appstruct['schemata']))
                    .all()))
            Session.add(export)
            Session.flush()
            task = tasks.make_export.subtask(args=(export.id,))
            # Avoid race-conditions by executing the task after
            # the current request completes successfully
            transaction.get().addAfterCommitHook(
                lambda success: success and task.apply_async())
            request.session.flash(
                _(u'Your request has been received!'), 'success')
            return HTTPFound(location=request.route_path('data_export'))

    layout = request.layout_manager.layout
    layout.title = _(u'Data')
    layout.set_nav('data_nav')

    schemata_query = (
        Session.query(models.Schema)
        .filter(models.Schema.publish_date != null())
        .order_by(
            models.Schema.name.asc(),
            models.Schema.publish_date.desc()))

    limit = request.registry.settings.get('app.export_limit')
    exceeded = False

    if limit:
        exports_count = query_exports(request).count()
        if exports_count >= int(limit):
            exceeded = True
            request.session.flash(
                _(u'You have exceed your export limit of ${limit}',
                    mapping={'limit': limit}),
                'warning')

    return {
        'exceeded': exceeded,
        'csrf_token': request.session.get_csrf_token(),
        'form': form,
        'schemata': schemata_query,
        'schemata_count': schemata_query.count()}


@view_config(
    route_name='data_export',
    permission='fia_view',
    renderer='occams.clinical:templates/data/export.pt')
def export(request):
    """
    Lists current export jobs.

    This is where the user can view the progress of the exports and download
    them at a later time.
    """
    layout = request.layout_manager.layout
    layout.title = _(u'Data')
    layout.set_nav('data_nav')

    export_expire = request.registry.settings.get('app.export_expire')
    duration = None

    if export_expire:
        delta = timedelta(int(export_expire))
        locale_name = negotiate_locale_name(request)
        duration = format_timedelta(delta, threshold=1, locale=locale_name)

    exports_query = query_exports(request)
    exports_count = exports_query.count()

    return {
        'duration': duration,
        'exports': exports_query,
        'exports_count': exports_count}


def query_exports(request):
    """
    Helper method to query current exports for the authenticated user
    """
    userid = authenticated_userid(request)
    export_expire = request.registry.settings.get('app.export_expire')

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


@view_config(
    route_name='data_download',
    permission='fia_view')
def download(request):
    """
    Returns specific download attachement

    The user should only be allowed to download their exports.
    """
    userid = authenticated_userid(request)

    try:
        export = (
            Session.query(models.Export)
            .filter_by(id=request.matchdict['export_id'], status='complete')
            .filter(models.Export.owner_user.has(key=userid))
            .one())
    except orm.exc.NoResultFound:
        raise HTTPNotFound

    export_dir = request.registry.settings['app.export_dir']
    path = os.path.join(export_dir, '%s.zip' % export.id)

    response = FileResponse(path)
    response.content_disposition = (
        'attachment;filename=clinical-%d.zip' % export.id)
    return response
