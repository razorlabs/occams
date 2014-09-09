from pyramid.httpexceptions import HTTPBadRequest, HTTPForbidden
from pyramid.view import view_config
from sqlalchemy import func, orm, sql
from voluptuous import *  # NOQA


from .. import _, models, Session


def view_json(context, request):
    cycle = context
    return {
        '__url__': request.route_path('cycle',
                                      study=cycle.study.name,
                                      cycle=cycle.name),
        'name': cycle.name,
        'title': cycle.title,
        'week': cycle.week,
        'is_interim': cycle.is_interim,
        'schemata': [{
            'id': schema.id,
            'name': schema.name,
            'title': schema.title,
            'publish_date': schema.publish_date.isoformat()
            } for schema in cycle.schemata]
        }


def edit_schemata_json(context, request):
    check_csrf_token(request)

    schema = Schema({
        Required('schemata', default=[]): [
            DatabaseEntry(
                models.Schema,
                path=['schema'],
                msg=_(u'Schema does not exist'),
                localizer=request.localizer),
            check_is_study_schema(context, request),
            ]})

    try:
        data = schema(requst.json_body)
    except MultipleInvalid as e:
        raise HTTPBadRequest(json={
            'validation_errors': [m.error_message for m in e.errors]})

    new_ids = set([s.id for s in data['schemata']])

    # Remove unused
    for schema in list(context.schemata):
        if schema.id not in new_ids:
            context.schemata.remove(schema)
        else:
            new_ids.remove(schema.id)

    # Update list
    context.schemata.extend([s for s in data['schemata'] if s.id in new_ids])

    return HTTPOk()


def check_is_study_schema(context, request):
    """
    Returns a validator that checks that the schema is part of the study
    """
    def validator(value):
        return value
    return validator
