from pyramid.i18n import get_localizer
from pyramid.httpexceptions import HTTPBadRequest, HTTPForbidden, HTTPOk
from pyramid.session import check_csrf_token
from pyramid.view import view_config
import six
import sqlalchemy as sa
from sqlalchemy import orm
from voluptuous import *  # NOQA

from .. import _, models, Session


@view_config(
    route_name='forms',
    permission='add',
    request_method='POST',
    request_param='forms',
    renderer='json')
def move_json(context, request):
    """
    'Moves' new forms into a new visit context
    """
    check_csrf_token(request)

    schema = Schema({
        'from_visit': coerce_visit(context, request),
        'forms': [coerce_entity(context, request)],
        Extra: object})

    try:
        data = schema(request.json_body)
    except MultipleInvalid as e:
        raise HTTPBadRequest(json={
            'validation_errors': [m.error_message for m in e.errors]})

    # Need to be able to edit both targets
    if not request.check_permission('edit', data['from_visit']):
        raise HTTPForbidden

    entity_ids = [entity.id for entity in data['forms']]

    (Session.query(models.Context)
        .filter(models.Context.entity_id.in_(entity_ids))
        .filter(models.Context.external == u'visit')
        .update({'key': context.id}, 'fetch'))

    (Session.query(models.Context)
        .filter(models.Context.entity_id.in_(entity_ids))
        .filter(models.Context.external == u'patient')
        .update({'key': context.patient.id}, 'fetch'))

    return HTTPOk()


def coerce_visit(context, request):
    """
    Returns a validator that converts an input value into a visit instance
    """
    def validator(value):
        lz = get_localizer(request)
        cycle = Session.query(models.Cycle).get(value)
        if not cycle:
            raise Invalid(lz.translate(
                _(u'Specified visit does not exist')),
                path=['cycle'])
        return cycle
    return validator



def coerce_entity(context, request):
    def validator(value):
        lz = get_localizer(request)
        entity = Session.query(models.Entity).get(value)
        if not entity:
            raise Invalid(lz.translate(
                _(u'Specified entity does not exist')),
                path=['form'])
    return validator
