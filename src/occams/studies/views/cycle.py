from good import *  # NOQA
from pyramid.httpexceptions import HTTPBadRequest, HTTPForbidden
from pyramid.session import check_csrf_token
from pyramid.view import view_config
import six

from .. import _, models, Session
from . import form as form_views
from ..validators import invalid2dict


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
        'id': cycle.id,
        'name': cycle.name,
        'title': cycle.title,
        'week': cycle.week,
        'is_interim': cycle.is_interim,
        'schemata': form_views.versions2json(cycle.schemata)
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
    except Invalid as e:
        raise HTTPBadRequest(json={'errors': invalid2dict(e)})

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

    return {
        '__next__': request.route_path('study', study=context.study.name),
        'message': _(u'Successfully removed "${cycle}"',
                     mapping={'cycle': context.title})
        }


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
            Type(*six.string_types),
            Coerce(six.binary_type),
            Length(min=3, max=32),
            check_unique_name),
        'title': All(
            Type(*six.string_types),
            Coerce(six.text_type),
            Length(min=3, max=32)),
        'week': Any(
            Coerce(int),
            All(Type(*six.string_types), Falsy(), Default(None)),
            Default(None)),
        'is_interim': Any(Boolean(), Default(False)),
        Extra: Remove})
