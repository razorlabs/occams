from pyramid.view import view_config

from .. import models, Session


@view_config(
    route_name='reference_type',
    permission='view',
    renderer='json')
def view_json(context, request):
    return {
        'id': context.id,
        'name': context.name,
        'title': context.title,
        'reference_pattern': context.reference_pattern,
        'reference_hint': context.reference_hint
    }


@view_config(
    route_name='reference_types',
    permission='view',
    xhr=True,
    request_param='vocabulary=available_reference_types',
    renderer='json')
def available_reference_types(context, request):
    term = (request.GET.get('term') or '').strip()

    query = Session.query(models.ReferenceType)

    if term:
        query = query.filter_by(
            models.ReferenceType.title.ilike('%' + term + '%'))

    query = query.order_by(models.ReferenceType.title.asc()).limit(100)

    return {
        '__query__': {'term': term},
        'reference_types': [view_json(reference_type, request)
                            for reference_type in query]
    }
