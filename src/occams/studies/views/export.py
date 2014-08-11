from datetime import datetime, timedelta
import os
import uuid

from babel.dates import format_datetime
from humanize import naturalsize
from pyramid.i18n import get_localizer, negotiate_locale_name
from pyramid.httpexceptions import (
    HTTPFound, HTTPNotFound, HTTPOk, HTTPForbidden)
from pyramid.response import FileResponse
from pyramid.settings import asbool
from pyramid.view import view_config
import six
from sqlalchemy import orm
import transaction
from wtforms import (
    Form,
    RadioField,
    SelectMultipleField,
    widgets,
    validators
)

from .. import _, log, models, Session, exports
from ..tasks import celery,  make_export
from ..widgets.pager import Pager
from ..security import CSRF


@view_config(
    route_name='exports',
    permission='fia_view',
    renderer='../templates/export/home.pt')
def about(request):
    """
    General intro-page so users know what they're getting into.
    """
    return {}


@view_config(
    route_name='exports_faq',
    permission='fia_view',
    renderer='../templates/export/faq.pt')
def faq(request):
    """
    Verbose details about how this tool works.
    """
    return {}


class ExportCheckoutForm(Form):
    """
    Export checkout serialization schema
    """

    class Meta(object):
        csrf = True
        csrf_class = CSRF

    contents = SelectMultipleField(
        widget=widgets.ListWidget(prefix_label=False),
        option_widget=widgets.CheckboxInput(),
        validators=[
            validators.required(_(u'Please select an item')),
            validators.Length(min=1),
        ])

    expand_collections = RadioField(
        label=_(u'Select list style.'),
        choices=[
            (False, _(u'Single column with comma-delimited values.')),
            (True, _(u'Separate column for each possible answer choice.'))
        ],
        coerce=asbool,
        default=False)

    use_choice_labels = RadioField(
        label=_(u'Select answer choice style.'),
        choices=[
            (False, _(u'Use codes.')),
            (True, _(u'Use labels.'))
        ],
        coerce=asbool,
        default=False)


@view_config(
    route_name='exports_checkout',
    permission='fia_view',
    renderer='../templates/export/add.pt')
def add(request):
    """
    Generating a listing of available data for export.

    Because the exports can take a while to generate, this view serves
    as a "checkout" page so that the user can select which files they want.
    The actual exporting process is then queued in a another thread so the user
    isn't left with an unresponsive page.
    """

    exportables = exports.list_all(include_rand=False)
    limit = request.registry.settings.get('app.export.limit')
    exceeded = limit is not None and query_exports(request).count() > limit

    form = ExportCheckoutForm(request.POST, meta={'csrf_context': request.session})
    form.contents.choices = [(k, v.title) for k, v in six.iteritems(exportables)]

    if request.method == 'POST' and not exceeded and form.validate():
        task_id = six.u(str(uuid.uuid4()))
        Session.add(models.Export(
            name=task_id,
            expand_collections=form.expand_collections.data,
            use_choice_labels=form.use_choice_labels.data,
            owner_user=(Session.query(models.User)
                        .filter_by(key=request.authenticated_userid)
                        .one()),
            contents=[exportables[k].to_json() for k in form.contents.data]))

        def apply_after_commit(success):
            if success:
                make_export.apply_async(
                    args=[task_id],
                    task_id=task_id,
                    countdown=4)

        # Avoid race-condition by executing the task after succesful commit
        transaction.get().addAfterCommitHook(apply_after_commit)

        msg = _(u'Your request has been received!')
        request.session.flash(msg, 'success')

        return HTTPFound(location=request.route_path('export_status'))

    return {
        'form': form,
        'exceeded': exceeded,
        'limit': limit,
        'exportables': exportables
    }


@view_config(
    route_name='exports_status',
    permission='fia_view',
    renderer='../templates/export/status.pt')
def status(request):
    """
    Renders the view that will contain progress of exports.

    All exports will be loaded asynchronously via seperate ajax call.
    """
    return {}


@view_config(
    route_name='exports_status',
    permission='fia_view',
    xhr=True,
    renderer='json')
def status_json(request):
    """
    Returns the current exports statuses.
    """

    exports_query = query_exports(request)
    exports_count = exports_query.count()

    pager = Pager(request.GET.get('page', 1), 5, exports_count)
    exports_query = exports_query[pager.slice_start:pager.slice_end]

    locale = negotiate_locale_name(request)
    localizer = get_localizer(request)

    def export2json(export):
        count = len(export.contents)
        return {
            'id': export.id,
            'title': localizer.pluralize(
                _(u'Export containing ${count} item'),
                _(u'Export containing ${count} items'),
                count, 'occams.studies', mapping={'count': count}),
            'name': export.name,
            'status': export.status,
            'use_choice_labels': export.use_choice_labels,
            'expand_collections': export.expand_collections,
            'contents': sorted(export.contents, key=lambda v: v['title']),
            'count': None,
            'total': None,
            'file_size': (naturalsize(export.file_size)
                          if export.file_size else None),
            'download_url': request.route_path('export_download',
                                               id=export.id),
            'delete_url': request.route_path('export_delete', id=export.id),
            'create_date': format_datetime(export.create_date, locale=locale),
            'expire_date': format_datetime(export.expire_date, locale=locale)
        }

    return {
        'csrf_token': request.session.get_csrf_token(),
        'pager': pager.serialize(),
        'exports': [export2json(e) for e in exports_query]
    }


@view_config(
    route_name='exports_codebook',
    permission='fia_view',
    renderer='../templates/export/codebook.pt')
def codebook(request):
    """
    Codebook viewer
    """
    return {'exportables': exports.list_all().values()}


@view_config(
    route_name='exports_codebook',
    permission='fia_view',
    xhr=True,
    renderer='json')
def codebook_json(request):
    """
    Loads codebook rows for the specified data file
    """

    file = request.GET.get('file')

    if not file:
        raise HTTPNotFound

    def massage(row):
        publish_date = row['publish_date']
        if publish_date:
            row['publish_date'] = publish_date.isoformat()
        return row

    exportables = exports.list_all()

    if file not in exportables:
        raise HTTPNotFound

    plan = exportables[file]
    return [massage(row) for row in plan.codebook()]


@view_config(
    route_name='exports_codebook',
    request_param='alt=json',
    permission='fia_view')
def codebook_download(request):
    """
    Returns full codebook file
    """
    export_dir = request.registry.settings['app.export.dir']
    codebook_name = exports.codebook.FILE_NAME
    path = os.path.join(export_dir, codebook_name)
    if not os.path.isfile(path):
        log.warn('Trying to download codebook before it\'s pre-cooked!')
        raise HTTPNotFound
    response = FileResponse(path)
    response.content_disposition = 'attachment;filename=%s' % codebook_name
    return response


@view_config(
    route_name='export',
    permission='fia_view',
    request_method='DELETE',
    xhr=True)
def delete(request):
    """
    Handles delete delete AJAX request
    """
    export = (
        Session.query(models.Export)
        .filter(models.Export.id == request.matchdict['id'])
        .filter(models.Export.owner_user.has(key=request.authenticated_userid))
        .first())

    if not export:
        raise HTTPNotFound

    if request.POST.get('csrf_token') != request.session.get_csrf_token():
        raise HTTPForbidden

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
            .filter(models.Export.owner_user.has(key=request.authenticated_userid))  # NOQA
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
