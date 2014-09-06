from uuid import uuid4
from pyramid.i18n import get_localizer
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.session import check_csrf_token
from pyramid.view import view_config
import six
import sqlalchemy as sa
from sqlalchemy import orm
from voluptuous import *  # NOQA

from .. import _, models, Session
from ..validators import Date


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
    route_name='visits_cycles',
    permission='view',
    xhr=True,
    renderer='json')
def cycles_json(context, request):
    """
    Searchs for cycles
    """

    schema = Schema({
        Required('q', default=''): lambda v: v.strip(),
        Required('ids', default=[]): [int],
        Extra: object
        })

    try:
        data = schema(request.GET.mixed())
    except MultipleInvalid as e:
        raise HTTPBadRequest(json=[str(m) for m in e.errors])

    q, ids = data['q'], data['ids']

    def query_cycles():
        query = (
            Session.query(models.Cycle)
            .join(models.Cycle.study))
        if ids:
            query = query.filter(models.Cycle.id.in_(ids))
        elif q:
            query = query.filter(models.Cycle.title.ilike('%%%s%%' % q))
        query = (
            query
            .order_by(models.Study.title, models.Cycle.week)
            .limit(25))
        return query

    return {
        'cycles': [] if not (q or ids) else [{
            'id': cycle.id,
            'title': cycle.title
            } for cycle in query_cycles()]}


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
            '__url__': request.route_path('visit_form',
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
    route_name='visits',
    permission='view',
    request_method='GET',
    request_param='cycles',
    xhr=True,
    renderer='json')
def validate_cycles(context, request):
    target = 'cycles'
    schema = VisitSchema(context, request)
    key = next(key for key in six.iterkeys(schema.schema)
               if str(key) == target)
    try:
        schema.schema[key](request.GET[target].split(','))
    except MultipleInvalid as e:
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
    except MultipleInvalid as e:
        raise HTTPBadRequest(json={
            'validation_errors': [m.error_message for m in e.errors]})
    if isinstance(context, models.VisitFactory):
        visit = models.Visit(patient=context.__parent__)
        Session.add(visit)
    else:
        visit = context

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
            .join(models.Cycle, models.Cycle.schemata)
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
                ~model.Schema.name.in_(
                    [entity.schema.name for entity in visit.entities]))

        for schema in schemata_query:
            visit.entities.append(model.Entity(
                name=str(uuid4()),
                title=schema.title,
                schema=schema,
                collect_date=data['visit_date'],
                state=default_state))

    Session.flush()

    return view_json(visit, request)


def VisitSchema(context, request):
    lz = get_localizer(request)
    return Schema({
        Required('cycles'): All(
            [All(coerce_cycle(context, request),
                 unique_cycle(context, request))],
            Length(
                min=1,
                msg=lz.translate(_(u'Must select at least one cycle')))),
        Required('visit_date'):
            All(Date(), unique_visit_date(context, request)),
        Required('include_forms', default=False): Boolean(),
        Required('include_specimen', default=False): Boolean(),
        Extra: object
        })


def coerce_cycle(context, request):
    """
    Returns a validator that converts an input value into a cycle instance
    """
    def validator(value):
        lz = get_localizer(request)
        cycle = Session.query(models.Cycle).get(value)
        if not cycle:
            raise Invalid(lz.translate(
                _(u'Specified cycle does not exist')),
                path=['cycle'])
        return cycle
    return validator


def unique_cycle(context, request):
    """
    Returns a validator callback to ensure the cycle has not already been used
    """
    def validator(value):
        lz = get_localizer(request)
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
            raise Invalid(lz.translate(
                _(u'\'${cycle}\' is already used by visit ${visit_date}'),
                mapping={
                    'cycle': value.title,
                    'visit_date': taken.visit_date}),
                path=['cycle'])
        return value
    return validator


def unique_visit_date(context, request):
    """
    Returns a validator callback to check for date uniqueness
    """
    def validator(value):
        lz = get_localizer(request)
        exists_query = (
            Session.query(models.Visit)
            .filter_by(visit_date=value))
        if isinstance(context, models.Visit):
            exists_query = exists_query.filter(models.Visits.id != context.id)
        exists, = Session.query(exists_query.exists()).one()
        if exists:
            raise Invalid(lz.translate(_(u'Visit already exists')))
        return value
    return validator
