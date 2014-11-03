from pyramid.view import view_config

from .. import models, Session


@view_config(
    route_name='site',
    permission='view',
    renderer='json')
def view_json(context, request):
    return {
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
