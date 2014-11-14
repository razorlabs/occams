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
from ..validators import Bytes, String, invalid2dict


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
        context.name, context.publish_date.isoformat())
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


def VersionSchema(context, request):
    return Schema({
        'name': Bytes(),
        'title': All(String(), Length(min=3, max=128)),
        Optional('description'): String(),
        # TODO: Need to check that it's unique, no time
        'publish_date': Date(),
        Extra: Remove
        })
