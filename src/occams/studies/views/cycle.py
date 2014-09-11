from pyramid.httpexceptions import HTTPBadRequest, HTTPForbidden
from pyramid.session import check_csrf_token
from pyramid.view import view_config
import six
from voluptuous import *  # NOQA

from .. import _, models, Session


@view_config(
    route_name='cycle',
    permission='view',
    xhr=True,
    renderer='json')
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


@view_config(
    route_name='cycles',
    permission='add',
    request_method='POST',
    xhr=True,
    renderer='json')
@view_config(
    route_name='cycle',
    permission='edit',
    request_method='PUT',
    xhr=True,
    renderer='json')
def edit_json(context, request):
    check_csrf_token(request)

    schema = CycleSchema(context, request)

    try:
        data = schema(request.json_body)
    except MultipleInvalid as e:
        raise HTTPBadRequest(json={
            'validation_errors': [m.error_message for m in e.errors]})

    if isinstance(context, models.CycleFactory):
        cycle = models.Cycle(study=context.__parent__)
        Session.add(cycle)
    else:
        cycle = context

    cycle.name = data['name']
    cycle.title = data['title']
    cycle.week = data['week']
    cycle.is_interim = data['is_interim']

    Session.flush()

    return view_json(cycle, request)


@view_config(
    route_name='cycle',
    permission='delete',
    request_method='DELETE',
    xhr=True,
    renderer='json')
def delete_json(context, request):
    check_csrf_token(request)

    (has_visits,) = (
        Session.query(
            Session.query(models.Visit)
            .filter(models.Visit.cycles.any(id=context.id))
            .exists())
        .one())

    if has_visits and not request.has_permission('admin', context):
        raise HTTPForbidden(_(u'Cannot delete a cycle with visits'))

    Session.delete(context)
    Session.flush()

    request.session.flash(
        _(u'Successfully removed "${cycle}"', mapping={
            'cycle': context.title}))

    return {'__next__': request.route_path('study', study=context.study.name)}


def CycleSchema(context, request):

    def check_unique_name(value):
        query = Session.query(models.Cycle).filter_by(name=value)
        if isinstance(context, models.Cycle):
            query = query.filter(models.Cycle.id != context.id)
        (exists,) = Session.query(query.exists()).one()
        if exists:
            msg = _('"${name}" already exists')
            mapping = {'name': value}
            raise Invalid(request.localizer.translate(msg, mapping=mapping))
        return value

    return Schema({
        'name': All(
            Coerce(six.binary_type),
            Length(min=3, max=32),
            check_unique_name),
        'title': All(Coerce(six.text_type), Length(min=3, max=32)),
        'week': Coerce(int),
        Required('is_interim', default=False): Boolean(),
        Extra: object})
