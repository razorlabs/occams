from pyramid.httpexceptions import HTTPBadRequest
from pyramid.session import check_csrf_token
from pyramid.view import view_config
from sqlalchemy import func, orm
import six
from voluptuous import *  # NOQA

from .. import _, models, Session
from . import cycle as cycle_views

unicode = sys.versionk


@view_config(
    route_name='home',
    permission='view',
    renderer='../templates/study/list.pt')
def home(request):
    studies_query = (
        Session.query(models.Study)
        .order_by(models.Study.title.asc()))

    modified_query = (
        Session.query(models.Patient)
        .order_by(models.Patient.modify_date.desc())
        .limit(10))

    viewed = sorted((request.session.get('viewed') or {}).values(),
                    key=lambda v: v['view_date'],
                    reverse=True)

    return {
        'studies': studies_query,
        'studies_count': studies_query.count(),

        'modified': modified_query,
        'modified_count': modified_query.count(),

        'viewed': viewed,
        'viewed_count': len(viewed),
    }


@view_config(
    route_name='study',
    permission='view',
    renderer='../templates/study/view.pt')
def view(context, request):
    return {
        'study': view_json(context, request)
        }


@view_config(
    route_name='study',
    permission='view',
    renderer='json')
def view_json(context, request):
    study = context
    return {
        '__url__': request.route_path('study', study=study.name),
        'id': study.id,
        'name': study.name,
        'title': study.title,
        'code': study.code,
        'short_title': study.short_title,
        'start_date': study.start_date and study.start_date.isoformat(),
        'stop_date': study.stop_date and study.stop_date.isoformat(),
        'consent_date': study.consent_date.isoformat(),
        'schemata': [{
            'id': schema.id,
            'name': schema.name,
            'title': schema.title,
            'publish_date': schema.publish_date.isoformat()
            } for schema in study.schemata],
        'cycles': [
            cycle_views.view_json(cycle, request) for cycle in study.cycles]
        }


@view_config(
    route_name='study_progress',
    permission='view',
    renderer='../templates/study/progress.pt')
def progress(context, request):

    states_query = Session.query(models.State)

    VisitCycle = orm.aliased(models.Cycle)

    cycles_query = (
        Session.query(models.Cycle)
        .filter_by(study=context)
        .add_column(
            Session.query(func.count(models.Visit.id))
            .join(VisitCycle, models.Visit.cycles)
            .filter(VisitCycle.id == models.Cycle.id)
            .correlate(models.Cycle)
            .label('visits_count')))

    for state in states_query:
        cycles_query = cycles_query.add_column(
            Session.query(func.count(models.Visit.id))
            .join(VisitCycle, models.Visit.cycles)
            .filter(models.Visit.entities.any(state=state))
            .filter(VisitCycle.id == models.Cycle.id)
            .correlate(models.Cycle)
            .label(state.name))

    cycles_query = cycles_query.order_by(models.Cycle.week.asc())
    cycles_count = context.cycles.count()

    return {
        'states': states_query,
        'cycles': cycles_query,
        'cycles_count': cycles_count,
        'has_cycles': cycles_count > 0}


@view_config(
    route_name='studies',
    permission='add',
    request_method='POST',
    xhr=True,
    renderer='json')
@view_config(
    route_name='study',
    permission='edit',
    request_method='PUT',
    xhr=True,
    renderer='json')
def edit_json(context, request):
    check_csrf_token(request)

    schema = StudySchema(context, request)

    try:
        data = schema(request.json_body)
    except MultipleInvalid as e:
        raise HTTPBadRequest(json={
            'validation_errors': [m.error_message for m in e.errors]})

    if isinstance(context, models.StudyFactory):
        study = models.Study()
        Session.add(study)
    else:
        study = context

    study.name = data['name']
    study.title = data['title']
    study.code = data['code']
    study.short_title = data['short_title']
    study.consent_date = data['consent_date']
    study.start_date = data['start_date']
    study.stop_date = data['stop_date']

    Session.flush()

    request.session.flash(_(u'New study added!', 'success'))

    return view_json(study, request)


@view_config(
    route_name='study',
    permission='edit',
    request_method='PUT',
    request_param='schemata',
    xhr=True,
    renderer='json')
def edit_schemata_json(context, request):
    check_csrf_token(request)

    schema = Schema({
        Required('schemata', default=[]): [
            DatabaseEntry(
                models.Schema,
                path=['schema'],
                msg=_(u'Schema does not exist'),
                localizer=request.localizer)]})

    try:
        data = schema(requst.json_body)
    except MultipleInvalid as e:
        raise HTTPBadRequest(json={
            'validation_errors': [m.error_message for m in e.errors]})

    new_ids = set([s.id for s in data['schemata']])
    old_ids = set()

    # Remove unused
    for schema in list(context.schemata):
        if schema.id not in new_ids:
            context.schemata.remove(schema)
            old_ids.add(schema.id)
        else:
            new_ids.remove(schema.id)

    # Update list
    context.schemata.extend([s for s in data['schemata'] if s.id in new_ids])

    # Update cycles to stay as a subset of study forms
    (Session.query(models.cycle_schema_table)
        .filter(~models.cycle_schema_table.c.schema_id.in_(old_ids))
        .filter(models.cycle_schema_table.c.cycle_id.in_(
            Session.query(models.Cycle.id)
            .filter_by(study=context)
            .subquery()))
        .delete())

    return HTTPOk()


def StudySchema(context, request):
    return Schema({
        'name': All(
            Coerce(six.binary_type),
            Length(min=3, max=32),
            check_unique(context, request)),
        'title': All(Coerce(six.text_type), Length(min=3, max=32)),
        'code': All(Coerce(six.binary_type), Length(min=3, max=8)),
        'short_title': All(Coerce(six.binary_type), Length(min=3, max=8)),
        'consent_date': Date(),
        Required('start_date', default=None): Date(),
        Required('stop_date', default=None): Date(),
        Extra: object})


def check_unique(context, request):
    """
    Returns a validator that checks if the study name is unique
    """
    def validator(value):
        query = (
            Session.query(models.Study)
            .filter_by(name=name))
        if isinstance(context, models.Study):
            query = query.filter_by(models.Study.id != value.id)
        (exists,) = Session.query(query.exists()).one()
        if exists:
            lz = get_localizer(request)
            msg = _('"${name}" already exists')
            mapping = {'name': value}
            raise Invalid(lz.translate(msg, mapping=mapping))
        return value
    return validator
