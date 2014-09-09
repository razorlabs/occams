from pyramid.httpexceptions import HTTPBadRequest, HTTPOk
from pyramid.session import check_csrf_token
from pyramid.view import view_config
from voluptuous import *  # NOQA

from .. import _, models, Session
from ..validators import DatabaseEntry


@view_config(
    route_name='forms',
    permission='add',
    request_method='POST',
    renderer='json')
def add_json(context, request):
    check_csrf_token(request)

    schema = Schema({
        'schemata': [All(
            DatabaseEntry(
                models.Schema,
                msg=_(u'Schema does not exist'),
                path=['schema'],
                localizer=request.localizer),
            check_study_form(context, request))],
        Extra: object})

    try:
        data = schema(request.json_body)
    except MultipleInvalid as e:
        raise HTTPBadRequest(json={
            'validation_errors': [m.error_message for m in e.errors]})

    default_state = (
        Session.query(models.State)
        .filter_by(name='pending-entry')
        .one())

    for schema in data['schemata']:
        entity = models.Entity(
            schema=schema,
            collect_date=context.__parent__.visit_date,
            state=default_state)
        context.__parent__.entities.add(entity)
        context.__parent__.patient.entities.add(entity)

    Session.flush()

    return HTTPOk()


@view_config(
    route_name='forms',
    permission='delete',
    request_method='DELETE',
    renderer='json')
def delete_json(context, request):
    """
    Deletes forms in bulk
    """
    check_csrf_token(request)

    schema = Schema({
        'forms': [DatabaseEntry(
            models.Entity,
            msg=_(u'Form does not exist'),
            localizer=request.localizer)],
        Extra: object})

    try:
        data = schema(request.json_body)
    except MultipleInvalid as e:
        raise HTTPBadRequest(json={
            'validation_errors': [m.error_message for m in e.errors]})

    entity_ids = [entity.id for entity in data['forms']]

    (Session.query(models.Entity)
        .filter(models.Entity.id.in_(
            Session.query(models.Context.entity_id)
            .filter(models.Context.entity_id.in_(entity_ids))
            .filter(models.Context.external == u'visit')
            .filter(models.Context.key == context.__parent__.id)))
        .delete('fetch'))

    Session.flush()

    return HTTPOk()


def check_study_form(context, request):
    """
    Returns a validator that checks if a form is allowed by the cycles/study
    """
    def validator(value):
        query = (
            Session.query(models.Visit)
            .filter(models.Visit.id == context.__parent__.id)
            .join(models.Visit.cycles)
            .join(models.Cycle.study)
            .filter(
                models.Cycle.schemata.any(id=value.id)
                | models.Study.schemata.any(id=value.id)))
        (exists,) = Session.query(query.exists()).one()
        if not exists:
            lz = request.localizer
            raise Invalid(lz.translate(
                _('${schema} is not part of the studies for this visit'),
                mapping={'schema': value.title}),
                path=['schema'])
        return value
    return validator
