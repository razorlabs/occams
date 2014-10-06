from datetime import datetime

from pyramid.httpexceptions import HTTPBadRequest
from pyramid.session import check_csrf_token
from pyramid.view import view_config
import sqlalchemy as sa
from sqlalchemy import orm
from good import *  # NOQA

from .. import _, models, Session
from ..validators import invalid2dict, Model


@view_config(
    route_name='visits',
    permission='view',
    xhr=True,
    renderer='json')
def list_json(context, request):
    patient = context.__parent__

    visits_query = (
        Session.query(models.Visit)
        .options(
            orm.joinedload(models.Visit.cycles).joinedload(models.Cycle.study))
        .filter_by(patient=patient)
        .order_by(models.Visit.visit_date.desc()))

    return {
        'visits': [
            view_json(v, request) for v in visits_query]
        }


@view_config(
    route_name='visit',
    permission='view',
    renderer='../templates/visit/view.pt')
def view(context, request):
    return {
        'visit': view_json(context, request)
        }


@view_config(
    route_name='visit',
    permission='view',
    xhr=True,
    renderer='json')
def view_json(context, request):
    visit = context
    entities_query = (
        Session.query(models.Entity)
        .options(orm.joinedload('schema'), orm.joinedload('state'))
        .join(models.Context)
        .filter_by(external='visit', key=visit.id))

    return {
        '__url__': request.route_path('visit',
                                      patient=visit.patient.pid,
                                      visit=visit.visit_date.isoformat()),
        'id': visit.id,
        'cycles': [{
            'id': cycle.id,
            'study': {
                'id': cycle.study.id,
                'name': cycle.study.name,
                'title': cycle.study.title,
                'code': cycle.study.code
                },
            'name': cycle.name,
            'title': cycle.title,
            'week': cycle.week
            } for cycle in visit.cycles],
        'patient': {
            '__url__': request.route_path('patient',
                                          patient=visit.patient.pid),
            'site': {
                'title': visit.patient.site.title,
                },
            'pid': visit.patient.pid
            },
        'visit_date': visit.visit_date.isoformat(),
        'entities': [{
            '__url__': request.route_path('form',
                                          patient=visit.patient.id,
                                          visit=visit.visit_date.isoformat(),
                                          form=entity.id),
            'id': entity.id,
            'schema': {
                'name': entity.schema.name,
                'title': entity.schema.title,
                },
            'collect_date': entity.collect_date.isoformat(),
            'not_done': entity.not_done,
            'state': {
                'id': entity.state.id,
                'name': entity.state.name,
                'title': entity.state.title,
                }
            } for entity in entities_query]
        }


@view_config(
    route_name='visits_cycles',
    permission='view',
    xhr=True,
    renderer='json')
def cycles_json(context, request):
    """
    AJAX handler for cycle field options
    """
    data = {'cycles': []}

    query = (
        Session.query(models.Cycle)
        .join(models.Cycle.study))

    if 'ids' in request.GET:
        query = query.filter(models.Cycle.id.in_(
            list(map(int, request.GET.getall('ids')))))
    elif 'q' in request.GET:
        query = query.filter(
            models.Cycle.title.ilike(u'%%%s%%' % request.GET['q']))
    else:
        return data

    query = (
        query
        .order_by(models.Study.title, models.Cycle.week)
        .limit(25))

    data['cycles'] = [{
        'id': cycle.id,
        'title': cycle.title
        } for cycle in query]

    return data


@view_config(
    route_name='visits',
    permission='view',
    request_method='GET',
    request_param='cycles',
    xhr=True,
    renderer='json')
def validate_cycles(context, request):
    """
    AJAX handler for validating cycles field
    """
    schema = VisitSchema(context, request)
    try:
        schema.compiled.schema['cycles'](request.GET.getall('cycles'))
    except Invalid as e:
        return str(e.message)
    return True


@view_config(
    route_name='visits',
    permission='add',
    request_method='POST',
    xhr=True,
    renderer='json')
@view_config(
    route_name='visit',
    permission='edit',
    request_method='PUT',
    xhr=True,
    renderer='json')
def edit_json(context, request):
    check_csrf_token(request)
    schema = VisitSchema(context, request)
    try:
        data = schema(request.json_body)
    except Invalid as e:
        raise HTTPBadRequest(json={'errors': invalid2dict(e)})
    if isinstance(context, models.VisitFactory):
        visit = models.Visit(patient=context.__parent__)
        Session.add(visit)
    else:
        visit = context

    visit.patient.modify_date = datetime.now()
    visit.cycles = data['cycles']
    visit.visit_date = data['visit_date']

    # TODO: Cannot hard code this
    default_state = (
        Session.query(models.State)
        .filter_by(name='pending-entry').one())

    if isinstance(context, models.Visit):
        for entity in visit.entities:
            if entity.state.name != default_state:
                entity.collect_date = data['visit_date']

    if data['include_forms']:
        CurrentSchema = orm.aliased(models.Schema)
        schemata_query = (
            Session.query(models.Schema)
            .select_from(models.Cycle)
            .join(models.Cycle.schemata)
            .filter(models.Schema.publish_date <= data['visit_date'])
            .filter(models.Schema.publish_date == (
                Session.query(sa.func.max(CurrentSchema.publish_date))
                .filter(CurrentSchema.name == models.Schema.name)
                .correlate(models.Schema)
                .as_scalar()))
            .filter(models.Cycle.id.in_([c.id for c in data['cycles']])))

        if isinstance(context, models.Visit):
            # Ignore already-added schemata
            schemata_query = schemata_query.filter(
                ~models.Schema.name.in_(
                    [entity.schema.name for entity in visit.entities]))

        for schema in schemata_query:
            visit.entities.add(models.Entity(
                schema=schema,
                collect_date=data['visit_date'],
                state=default_state))

    Session.flush()

    return view_json(visit, request)


@view_config(
    route_name='visit',
    permission='delete',
    request_method='DELETE',
    renderer='json')
def delete_json(context, request):
    check_csrf_token(request)
    list(map(Session.delete, context.entities))
    context.patient.modify_date = datetime.now()
    Session.delete(context)
    Session.flush()
    request.session.flash(_(
        u'Sucessfully deleted ${visit_date}',
        mapping={'visit_date': context.visit_date}))
    return {'__next__': request.route_path('patient',
                                           patient=context.patient.pid)}


def VisitSchema(context, request):

    def unique_cycle(value):
        if isinstance(context, models.Visit):
            patient = context.patient
        else:
            patient = context.__parent__
        taken_query = (
            Session.query(models.Visit)
            .filter(models.Visit.patient == patient)
            .filter(models.Visit.cycles.any(
                id=value.id, is_interim=sa.sql.false())))
        if isinstance(context, models.Visit):
            taken_query = taken_query.filter(models.Visit.id != context.id)
        taken = taken_query.first()
        if taken:
            msg = _(u'\'${cycle}\' is already used by visit ${visit_date}')
            mapping = {'cycle': value.title, 'visit_date': taken.visit_date}
            raise Invalid(request.localizer.translate(msg, mapping=mapping))
        return value

    def unique_visit_date(value):
        exists_query = (
            Session.query(models.Visit)
            .filter_by(visit_date=value))
        if isinstance(context, models.Visit):
            exists_query = exists_query.filter(models.Visit.id != context.id)
        exists, = Session.query(exists_query.exists()).one()
        if exists:

            msg = _(u'Visit already exists')
            raise Invalid(request.localizer.translate(msg))
        return value

    return Schema({
        'cycles': All(
            [All(
                Model(models.Cycle, localizer=request.localizer),
                unique_cycle)],
            Length(min=1)),
        'visit_date': All(Date('%Y-%m-%d'), unique_visit_date),
        'include_forms': Any(Boolean(), Default(False)),
        'include_specimen': Any(Boolean(), Default(False)),
        Extra: Remove
        })
