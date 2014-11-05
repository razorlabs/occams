from good import *  # NOQA
import six
from pyramid.httpexceptions import HTTPBadRequest, HTTPOk
from pyramid.session import check_csrf_token
from pyramid.view import view_config

from .. import _, models, Session
from ..validators import invalid2dict


@view_config(
    route_name='sites',
    permission='view',
    xhr=True,
    renderer='json')
def list_json(context, request):

    sites_query = Session.query(models.Site).order_by(models.Site.title.asc())

    return {
        'sites': [view_json(site, request)
                  for site in sites_query
                  if request.has_permission('view', site)]
        }


@view_config(
    route_name='site',
    xhr=True,
    permission='view',
    renderer='json')
def view_json(context, request):
    return {
        '__url__': request.route_path('site', site=context.name),
        'id': context.id,
        'name': context.name,
        'title': context.title
    }


@view_config(
    route_name='sites',
    permission='view',
    xhr=True,
    request_param='vocabulary=available_sites',
    renderer='json')
def available_sites(context, request):
    term = (request.GET.get('term') or '').strip()

    query = Session.query(models.Site)

    if term:
        query = query.filter_by(models.Site.title.ilike('%' + term + '%'))

    query = query.order_by(models.Site.title.asc()).limit(100)

    return {
        '__query__': {'term': term},
        'sites': [view_json(site, request)
                  for site in query
                  if request.has_permission('view', site)]
    }


@view_config(
    route_name='sites',
    permission='add',
    request_method='POST',
    xhr=True,
    renderer='json')
@view_config(
    route_name='site',
    permission='edit',
    request_method='PUT',
    xhr=True,
    renderer='json')
def edit_json(context, request):
    check_csrf_token(request)

    schema = SiteSchema(context, request)

    try:
        data = schema(request.json_body)
    except Invalid as e:
        raise HTTPBadRequest(json=invalid2dict(e))

    if isinstance(context, models.Site):
        site = context
    else:
        site = models.Site()
        Session.add(site)

    site.name = data['name']
    site.title = data['title']
    Session.flush()

    return view_json(site, request)


@view_config(
    route_name='site',
    permission='delete',
    request_method='DELETE',
    xhr=True,
    renderer='json')
def delete_json(context, request):
    check_csrf_token(request)
    Session.delete(context)
    Session.flush()
    msg = _(u'Successfully deleted: ${site}', mapping={'site': context.title})
    request.session.flash(msg)
    return HTTPOk(body=msg)


def SiteSchema(context, request):

    def unique_name(value):
        query = Session.query(models.Site).filter_by(name=value)
        if isinstance(context, models.Site):
            query = query.filter(models.Site.id != context.id)
        (exists,) = Session.query(query.exists()).one()
        if exists:
            msg = _(u'Site name already exists')
            raise Invalid(request.localizer.translate(msg))
        return value

    return Schema({
        'name': All(
            Type(*six.string_types),
            Coerce(six.binary_type),
            unique_name),
        'title': All(Type(*six.string_types), Coerce(six.text_type)),
        Extra: Remove
        })
