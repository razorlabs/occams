from collections import defaultdict
from datetime import datetime, timedelta
import os.path
import uuid

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

        id = colander.SchemaNode(colander.String())


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
        # Organize inputs since we're manually rendering forms
        inputs = {
            'schemata': request.POST.getall('schemata'),
            'csrf_token': request.POST.getone('csrf_token'),
            'expand_collections': request.POST.getone('expand_collections'),
            'use_choice_labels': request.POST.getone('use_choice_labels')}

        try:
            appstruct = form.validate(inputs.items())
        except deform.ValidationFailure as e:
            form = e
        else:
            export = models.Export(
                expand_collections=appstruct['expand_collections'],
                use_choice_labels=appstruct['use_choice_labels'],
                file_name=uuid.uuid4(),
                owner_user=(
                    Session.query(models.User)
                    .filter_by(key=authenticated_userid(request))
                    .one()),
                schemata=(
                    Session.query(models.Schema)
                    .filter(models.Schema.name.in_(appstruct['schemata']))
                    .filter(models.Schema.publish_date != null())
                    .filter(models.Schema.retract_date == null())
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

    schemata_query = query_schemata()
    versions = get_versions()

    return {
        'exceeded': exceeded,
        'csrf_token': request.session.get_csrf_token(),
        'form': form,
        'schemata': schemata_query,
        'versions': versions,
        'schemata_count': schemata_query.count()}


def query_schemata():
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
    path = os.path.join(export_dir, export.file_name)

    response = FileResponse(path)
    response.content_disposition = (
        'attachment;filename=clinical-%s.zip' % export.file_name)
    return response
