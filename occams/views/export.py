from datetime import datetime, timedelta
import json
import os
import uuid

from babel.dates import format_datetime
from humanize import naturalsize
from pyramid.i18n import get_localizer, negotiate_locale_name
from pyramid.httpexceptions import HTTPBadRequest, HTTPFound, HTTPOk
from pyramid.response import FileResponse
from pyramid.csrf import check_csrf_token
from pyramid.view import view_config
import transaction
import wtforms

from .. import _, log, models, exports, tasks
from ..utils.forms import wtferrors, Form
from ..utils.pagination import Pagination


@view_config(
    route_name='studies.exports',
    permission='view',
    renderer='../templates/export/home.pt')
def about(context, request):
    """
    General intro-page so users know what they're getting into.
    """
    return {}


@view_config(
    route_name='studies.exports_faq',
    permission='view',
    renderer='../templates/export/faq.pt')
def faq(context, request):
    """
    Verbose details about how this tool works.
    """
    return {}


@view_config(
    route_name='studies.exports_checkout',
    permission='add',
    renderer='../templates/export/checkout.pt')
def checkout(context, request):
    """
    Generating a listing of available data for export.

    Because the exports can take a while to generate, this view serves
    as a "checkout" page so that the user can select which files they want.
    The actual exporting process is then queued in a another thread so the user
    isn't left with an unresponsive page.
    """
    dbsession = request.dbsession
    exportables = exports.list_all(request.dbsession, include_rand=False)
    limit = request.registry.settings.get('app.export.limit')
    exceeded = limit is not None and query_exports(request).count() > limit
    errors = {}

    if request.method == 'POST' and check_csrf_token(request) and not exceeded:

        def check_exportable(form, field):
            if any(value not in exportables for value in field.data):
                raise wtforms.ValidationError(request.localizer.translate(
                    _(u'Invalid selection')))

        class CheckoutForm(Form):
            contents = wtforms.SelectMultipleField(
                choices=[(k, v.title) for k, v in exportables.items()],
                validators=[
                    wtforms.validators.InputRequired()])
            expand_collections = wtforms.BooleanField(default=False)
            use_choice_labels = wtforms.BooleanField(default=False)

        form = CheckoutForm(request.POST)

        if not form.validate():
            errors = wtferrors(form)
        else:
            task_id = str(uuid.uuid4())
            dbsession.add(models.Export(
                name=task_id,
                expand_collections=form.expand_collections.data,
                use_choice_labels=form.use_choice_labels.data,
                owner_user=(dbsession.query(models.User)
                            .filter_by(key=request.authenticated_userid)
                            .one()),
                contents=[exportables[k].to_json() for k in form.contents.data]
            ))

            def apply_after_commit(success):
                if success:
                    tasks.make_export.apply_async(
                        args=[task_id],
                        task_id=task_id,
                        countdown=4)

            # Avoid race-condition by executing the task after succesful commit
            transaction.get().addAfterCommitHook(apply_after_commit)

            msg = _(u'Your request has been received!')
            request.session.flash(msg, 'success')

            next_url = request.route_path('studies.exports_status')
            return HTTPFound(location=next_url)

    return {
        'errors': errors,
        'exceeded': exceeded,
        'limit': limit,
        'exportables': exportables
    }


@view_config(
    route_name='studies.exports_codebook',
    permission='view',
    renderer='../templates/export/codebook.pt')
def codebook(context, request):
    """
    Codebook viewer
    """
    dbsession = request.dbsession
    return {'exportables': exports.list_all(dbsession).values()}


@view_config(
    route_name='studies.exports_codebook',
    permission='view',
    xhr=True,
    renderer='json')
def codebook_json(context, request):
    """
    Loads codebook rows for the specified data file
    """
    dbsession = request.dbsession

    def massage(row):
        publish_date = row['publish_date']
        if publish_date:
            row['publish_date'] = publish_date.isoformat()
        return row

    exportables = exports.list_all(dbsession)

    file = request.GET.get('file')

    if file not in exportables:
        raise HTTPBadRequest(u'File specified does not exist')

    plan = exportables[file]
    return [massage(row) for row in plan.codebook()]


@view_config(
    route_name='studies.exports_codebook',
    request_param='alt=csv',
    permission='view')
def codebook_download(context, request):
    """
    Returns full codebook file
    """
    export_dir = request.registry.settings['studies.export.dir']
    codebook_name = exports.codebook.FILE_NAME
    path = os.path.join(export_dir, codebook_name)
    if not os.path.isfile(path):
        log.warn('Trying to download codebook before it\'s pre-cooked!')
        raise HTTPBadRequest(u'Codebook file is not ready yet')
    response = FileResponse(path)
    response.content_disposition = 'attachment;filename=%s' % codebook_name
    return response


@view_config(
    route_name='studies.exports_status',
    permission='view',
    renderer='../templates/export/status.pt')
def status(context, request):
    """
    Renders the view that will contain progress of exports.

    All exports will be loaded asynchronously via seperate ajax call.
    """
    return {}


@view_config(
    route_name='studies.exports_status',
    permission='view',
    xhr=True,
    renderer='json')
def status_json(context, request):
    """
    Returns the current exports statuses.
    """

    exports_query = query_exports(request)
    exports_count = exports_query.count()

    pagination = Pagination(request.GET.get('page', 1), 5, exports_count)
    exports_query = exports_query.offset(pagination.offset).limit(5)

    locale = negotiate_locale_name(request)
    localizer = get_localizer(request)

    redis = request.redis

    def export2json(export):
        # TODO: This doesn't actually work, I can't figure out how to get
        #       the corect data out of redis
        if export.status != 'complete':
            data = redis.hgetall(export.redis_key)
        else:
            data = {}
        log.debug('info: {}'.format(str(data)))
        count = len(export.contents)
        return {
            'id': export.id,
            'title': localizer.pluralize(
                _(u'Export containing ${count} item'),
                _(u'Export containing ${count} items'),
                count, 'occams', mapping={'count': count}),
            'name': export.name,
            'status': export.status,
            'use_choice_labels': export.use_choice_labels,
            'expand_collections': export.expand_collections,
            'contents': sorted(export.contents, key=lambda v: v['title']),
            'count': data.get('count'),
            'total': data.get('total'),
            'file_size': (naturalsize(export.file_size)
                          if export.file_size else None),
            'download_url': request.route_path('studies.export_download',
                                               export=export.id),
            'delete_url': request.route_path('studies.export',
                                             export=export.id),
            'create_date': format_datetime(export.create_date, locale=locale),
            'expire_date': format_datetime(export.expire_date, locale=locale)
        }

    return {
        'csrf_token': request.session.get_csrf_token(),
        'pager': pagination.serialize(),
        'exports': [export2json(e) for e in exports_query]
    }


@view_config(
    route_name='studies.exports_notifications',
    permission='view')
def notifications(context, request):
    """
    Yields server-sent events containing status updates of current exports
    REQUIRES GUNICORN WITH GEVENT WORKER
    """

    # Close DB connections so we don't hog them while polling
    request.dbsession.close()

    def listener():
        pubsub = request.redis.pubsub()
        pubsub.subscribe('export')

        # emit subsequent progress
        for message in pubsub.listen():

            if message['type'] != 'message':
                continue

            data = json.loads(message['data'])

            if data['owner_user'] != request.authenticated_userid:
                continue

            id = str(uuid.uuid4())
            event = 'progress'
            data = json.dumps(data)
            payload = f'id:{id}\nevent: {event}\ndata:{data}\n\n'
            log.debug(payload)

            # Note: app_iter seems to only work with bytes() data
            encoded = bytes(payload, encoding='utf-8')
            yield encoded

    response = request.response
    response.content_type = 'text/event-stream'
    response.cache_control = 'no-cache'
    # Set reverse proxies (if any, i.e nginx) not to buffer this connection
    response.headers['X-Accel-Buffering'] = 'no'
    response.app_iter = listener()

    return response


@view_config(
    route_name='studies.export',
    permission='delete',
    request_method='DELETE',
    xhr=True)
def delete_json(context, request):
    """
    Handles delete delete AJAX request
    """
    dbsession = request.dbsession
    check_csrf_token(request)
    export = context
    dbsession.delete(export)
    dbsession.flush()
    tasks.app.control.revoke(export.name)
    return HTTPOk()


@view_config(
    route_name='studies.export_download',
    permission='view')
def download(context, request):
    """
    Returns specific download attachement

    The user should only be allowed to download their exports.
    """
    export = context

    if export.status != 'complete':
        raise HTTPBadRequest('Export is not complete')

    export_dir = request.registry.settings['studies.export.dir']
    path = os.path.join(export_dir, export.name)

    response = FileResponse(path)
    response.content_disposition = 'attachment;filename=export.zip'
    return response


def query_exports(request):
    """
    Helper method to query current exports for the authenticated user
    """
    dbsession = request.dbsession
    userid = request.authenticated_userid
    export_expire = request.registry.settings.get('studies.export.expire') or 0

    query = (
        dbsession.query(models.Export)
        .filter(models.Export.owner_user.has(key=userid)))

    if export_expire > 0:
        cutoff = datetime.now() - timedelta(int(export_expire))
        query = query.filter(models.Export.modify_date >= cutoff)

    query = query.order_by(models.Export.create_date.desc())
    return query
