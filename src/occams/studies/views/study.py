from pyramid.httpexceptions import (
    HTTPNotFound, HTTPBadRequest, HTTPForbidden, HTTPOk)
from pyramid.session import check_csrf_token
from pyramid.view import view_config
from sqlalchemy import func, orm
import six
from voluptuous import *  # NOQA

from .. import _, models, Session
from . import cycle as cycle_views
from ..validators import Date, DatabaseEntry


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
    xhr=True,
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

    if isinstance(context, models.StudyFactory):
        request.session.flash(_(u'New study added!', 'success'))

    return view_json(study, request)


@view_config(
    route_name='study',
    permission='delete',
    request_method='DELETE',
    xhr=True,
    renderer='json')
def delete_json(context, request):
    check_csrf_token(request)

    (has_enrollments,) = (
        Session.query(
            Session.query(models.Enrollment)
            .filter_by(study=context)
            .exists())
        .one())

    if has_enrollments and not request.has_permission('admin', context):
        raise HTTPForbidden(_(u'Cannot delete a study with enrollments'))

    Session.delete(context)
    Session.flush()

    request.session.flash(
        _(u'Successfully removed "${study}"', mapping={
            'study': context.title}))

    return {'__next__': request.route_path('studies')}


@view_config(
    route_name='study_schemata',
    permission='edit',
    request_method='POST',
    xhr=True,
    renderer='json')
def add_schema_json(context, request):
    check_csrf_token(request)

    def check_not_patient_schema(value):
        (exists,) = (
            Session.query(
                Session.query(models.patient_schema_table)
                .filter(models.patient_schema_table.c.schema_id == value.id)
                .exists())
            .one())
        if exists:
            raise Invalid(request.localizer.translate(
                _(u'${schema} is already used as a patient form'),
                mapping={'schema': value.title}))
        return value

    def check_not_randomization_schema(value):
        if (context.randomization_schema is not None
                and context.randomization_schema == value):
            raise Invalid(request.localizer.translate(
                _(u'${schema} is already used as a randomization form'),
                mapping={'schema': value.title}))
        return value

    def check_not_termination_schema(value):
        if (context.termination_schema is not None
                and context.termination_schema == value):
            raise Invalid(request.localizer.translate(
                _(u'${schema} is already used as a termination form'),
                mapping={'schema': value.title}))
        return value

    schema = Schema({
        'schema': All(
            DatabaseEntry(
                models.Schema,
                path=['schema'],
                msg=_(u'Schema does not exist'),
                localizer=request.localizer),
            check_not_patient_schema,
            check_not_randomization_schema,
            check_not_termination_schema)})

    try:
        data = schema(request.json_body)
    except MultipleInvalid as e:
        raise HTTPBadRequest(json={
            'validation_errors': [m.error_message for m in e.errors]})

    context.schemata.add(data['schema'])

    return HTTPOk()


@view_config(
    route_name='study_schema',
    permission='edit',
    request_method='DELETE',
    xhr=True,
    renderer='json')
def delete_schema_json(context, request):
    check_csrf_token(request)
    schema = Session.query(models.Schema).get(request.matchdict['schema'])

    if schema is None:
        raise HTTPNotFound()

    # Remove from cycles
    Session.execute(
        models.cycle_schema_table.delete()
        .where(
            models.cycle_schema_table.c.cycle_id.in_(
                Session.query(models.Cycle.id)
                .filter_by(study=context)
                .subquery())
            & (models.cycle_schema_table.c.schema_id == schema.id)))

    # Remove from study
    Session.execute(
        models.study_schema_table.delete()
        .where(
            (models.study_schema_table.c.study_id == context.id)
            & (models.study_schema_table.c.schema_id == schema.id)))

    # Expire relations so they load their updated values
    Session.expire_all()

    return HTTPOk()


@view_config(
    route_name='study_schedule',
    permission='edit',
    request_method='PUT',
    xhr=True,
    renderer='json')
def edit_schedule_json(context, request):
    check_csrf_token(request)

    def check_schema_in_study(value):
        (exists,) = (
            Session.query(
                Session.query(models.Study)
                .filter(models.Study.cycles.any(study_id=context.id))
                .filter(models.Study.schemata.any(id=value.id))
                .exists())
            .one())
        if not exists:
            msg = _('${study} does not have form "${schema}"')
            mapping = {'schema': value.title, 'study': context.title}
            raise Invalid(request.localizer.translate(msg, mapping=mapping))
        return value

    def check_cycle_in_study(value):
        if value.study != context:
            msg = _('${study} does not have cycle "${cycle}"')
            mapping = {'cycle': value.title, 'study': context.title}
            raise Invalid(request.localizer.translate(msg, mapping=mapping))
        return value

    schema = Schema({
        'schema': All(
            DatabaseEntry(
                models.Schema,
                msg=_(u'Schema does not exist'),
                localizer=request.localizer),
            check_schema_in_study),
        'cycle': All(
            DatabaseEntry(
                models.Cycle,
                msg=_(u'Cycle does not exist'),
                localizer=request.localizer),
            check_cycle_in_study),
        'enabled': Boolean(),
        Extra: object,
        })

    try:
        data = schema(request.json_body)
    except MultipleInvalid as e:
        raise HTTPBadRequest(json={
            'validation_errors': [m.error_message for m in e.errors]})

    if data['enabled']:
        data['cycle'].schemata.add(data['schema'])
    else:
        data['cycle'].schemata.remove(data['schema'])

    return HTTPOk


def StudySchema(context, request):
    """
    Returns a validator for incoming study modification data
    """

    def check_unique_name(value):
        query = Session.query(models.Study).filter_by(name=value)
        if isinstance(context, models.Study):
            query = query.filter(models.Study.id != context.id)
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
        'code': All(Coerce(six.binary_type), Length(min=3, max=8)),
        'short_title': All(Coerce(six.text_type), Length(min=3, max=8)),
        'consent_date': Date(),
        Required('start_date', default=None): Date(),
        Required('stop_date', default=None): Date(),
        Extra: object})
