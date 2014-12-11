from copy import deepcopy
import json

from good import *  # NOQA
import six
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.response import FileIter
from pyramid.session import check_csrf_token
from pyramid.view import view_config

from .. import _, models, Session
from . import field as field_views
from ..validators import String, invalid2dict, Sanitize


@view_config(
    route_name='version',
    permission='view',
    renderer='../templates/version/view.pt')
def view(context, request):
    return {}


@view_config(
    route_name='version',
    xhr=True,
    renderer='json')
def view_json(context, request):
    """
    Edits form version metadata (not the fields)
    """
    return {
        '__url__': request.route_path(
            'version',
            form=context.name,
            version=str(context.publish_date or context.id)),
        '__types__': field_views.types,
        'id': context.id,
        'name': context.name,
        'title': context.title,
        'description': context.description,
        'publish_date': context.publish_date and str(context.publish_date),
        'retract_date': context.retract_date and str(context.retract_date),
        'fields': field_views.list_json(context['fields'], request)['fields'],
        }


@view_config(
    route_name='version',
    permission='view',
    request_param='download=json')
def download_json(context, request):
    fp = six.moves.cStringIO()
    json.dump(context.to_json(deep=True), fp, indent=2)
    fp.seek(0)
    response = request.response
    response.content_type = 'application/json'
    response.content_disposition = 'attachment; filename="%s-%s.json"' % (
        context.name,
        context.publish_date.isoformat() if context.publish_date else 'draft')
    response.app_iter = FileIter(fp)
    return response


@view_config(
    route_name='version_preview',
    permission='view',
    renderer='../templates/version/preview.pt')
def preview(context, request):
    """
    Preview form for test-drivining.
    """
    return {}


@view_config(
    route_name='version',
    xhr=True,
    permission='edit',
    request_method='PUT',
    request_param='publish',
    renderer='json')
def publish_json(context, request):
    check_csrf_token(request)

    def check_unique_publication(value):
        if value is not None:
            (exists,) = (
                Session.query(
                    Session.query(models.Schema)
                    .filter_by(name=context.name, publish_date=value)
                    .filter(models.Schema.id != context.id)
                    .exists())
                .one())
            if exists:
                msg = _('Version ${publish_date} is already in use')
                raise Invalid(request.localizer.translate(
                    msg, mapping={'publish_date': value}))
        return value

    def check_valid_timeline(value):
        if not value['publish_date'] and value['retract_date']:
            msg = _('No publish date set')
            raise Invalid(
                request.localizer.translate(msg), path=['retract_date'])
        if value['publish_date'] and value['retract_date'] \
                and value['retract_date'] < value['publish_date']:
            msg = _('Must be after publish date')
            raise Invalid(
                request.localizer.translate(msg), path=['retract_date'])
        return value

    validator = Schema(All({
        'publish_date': All(
            Sanitize(),
            Maybe(All(Date('%Y-%m-%d'), check_unique_publication))),
        'retract_date': All(Sanitize(), Maybe(Date('%Y-%m-%d'))),
        Extra: Remove
        },
        check_valid_timeline))

    try:
        data = validator(request.json_body)
    except Invalid as e:
        return HTTPBadRequest(json={'errors': invalid2dict(e)})

    context.publish_date = data['publish_date']
    context.retract_date = data['retract_date']

    Session.flush()

    return view_json(context, request)


@view_config(
    route_name='version',
    xhr=True,
    permission='edit',
    request_method='PUT',
    renderer='json')
def edit_json(context, request):
    check_csrf_token(request)

    validator = Schema({
        'title': All(String(), Length(min=3, max=128)),
        'description': Maybe(String()),
        Extra: Remove
        })

    try:
        data = validator(request.json_body)
    except Invalid as e:
        return HTTPBadRequest(json=invalid2dict(e))

    context.title = data['title']
    context.description = data['description']
    Session.flush()

    request.session.flash(_(u'Changes saved'), 'success')

    return view_json(context, request)


@view_config(
    route_name='version_editor',
    permission='edit',
    renderer='../templates/version/editor.pt')
def editor(context, request):
    return {}


@view_config(
    route_name='version',
    permission='draft',
    request_method='POST',
    request_param='draft',
    xhr=True,
    renderer='json')
def draft_json(context, request):
    """
    Drafts a new version of a published form.
    """
    check_csrf_token(request)
    schema = context
    if not schema.publish_date:
        raise HTTPBadRequest(json={
            'user_message': _(u'Cannot draft new from unpublished version')})
    draft = deepcopy(schema)
    Session.add(draft)
    Session.flush()
    request.session.flash(_(u'Successfully drafted new version'))
    return {
        # Hint the next resource to look for data
        '__next__': request.route_path('version_view',
                                       form=draft.name,
                                       version=draft.id)
        }


@view_config(
    route_name='version',
    permission='delete',
    request_method='DELETE',
    xhr=True,
    renderer='json')
def delete_json(context, request):
    """
    Edits form version metadata (not the fields)
    """
    check_csrf_token(request)

    Session.delete(context)

    if context.publish_date:
        msg = _(u'Successfully deleted ${name} version ${version}',
                mapping={'name': context.name,
                         'version': context.publish_date})
    else:
        msg = _(u'Successfully deleted draft of ${name}',
                mapping={'name': context.name})

    request.session.flash(msg)

    return {
        # Hint the next resource to look for data
        '__next__': request.current_route_path(_route_name='forms')
        }
