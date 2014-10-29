import csv
from datetime import date, timedelta
import mimetypes

from good import *  # NOQA
from pyramid.events import subscriber, BeforeRender
from pyramid.httpexceptions import \
    HTTPBadRequest, HTTPForbidden, HTTPNotFound, HTTPOk
from pyramid.session import check_csrf_token
from pyramid.view import view_config
import sqlalchemy as sa
from sqlalchemy import orm
import six
from zope.sqlalchemy import mark_changed

from .. import _, models, Session
from . import cycle as cycle_views, form as form_views
from ..validators import invalid2dict, Model
from ..utils import Pagination


@subscriber(BeforeRender)
def add_cores(event):
    """
    Inject studies listing into Chameleon template variables to render menu.
    """
    if event['renderer_info'].type != '.pt':
        return
    studies_query = Session.query(models.Study).order_by(models.Study.title)
    event.rendering_val['available_studies'] = studies_query.all()


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
    return {'study': view_json(context, request)}


@view_config(
    route_name='study',
    permission='view',
    xhr=True,
    renderer='json')
def view_json(context, request, deep=True):
    study = context
    data = {
        '__url__': request.route_path('study', study=study.name),
        'id': study.id,
        'name': study.name,
        'title': study.title,
        'code': study.code,
        'short_title': study.short_title,
        'consent_date': study.consent_date.isoformat(),
        'start_date': study.start_date and study.start_date.isoformat(),
        'end_date': study.end_date and study.end_date.isoformat(),
        'is_randomized': study.is_randomized,
        'is_blinded': study.is_blinded,
        'is_locked': study.is_locked,
        'termination_form':
            study.termination_schema
            and form_views.form2json(study.termination_schema),
        'randomization_form':
            study.randomization_schema
            and form_views.form2json(study.randomization_schema),
        }

    if deep:
        data.update({
            'cycles': [
                cycle_views.view_json(cycle, request)
                for cycle in study.cycles],
            'forms': form_views.form2json(study.schemata)})

    return data


@view_config(
    route_name='study_enrollments',
    permission='view',
    renderer='../templates/study/enrollments.pt')
def enrollments(context, request):
    """
    Displays enrollment summary and allows the user to filter by date.
    """

    result = (
        Session.query(sa.func.max(models.Cycle.week).label('week'))
        .filter_by(study=context)
        .first())

    if result and result.week > 0:
        duration = timedelta(days=result.week * 7)
    else:
        duration = timedelta.max

    statuses = {
        'active': models.Enrollment.termination_date == sa.null(),
        'terminated': models.Enrollment.termination_date != sa.null(),
        'termination_overdue': (
            (models.Enrollment.termination_date == sa.null())
            & (models.Enrollment.consent_date + duration < date.today())),
        'consent_overdue': (
            (models.Enrollment.termination_date == sa.null())
            & (models.Enrollment.latest_consent_date
                < models.Study.consent_date))
        }

    enrollments_query = (
        Session.query(
            models.Patient.pid,
            models.Enrollment.reference_number,
            models.Enrollment.consent_date,
            models.Enrollment.latest_consent_date,
            models.Enrollment.termination_date)
        .add_columns(*[expr.label(name) for name, expr in statuses.items()])
        .select_from(models.Enrollment)
        .join(models.Enrollment.patient)
        .join(models.Enrollment.study)
        .filter(models.Enrollment.study == context)
        .order_by(models.Enrollment.consent_date.desc()))

    schema = Schema({
        'page': Any(Coerce(int), Fallback(None)),
        'status': Any(In(statuses), Fallback(None)),
        'start': Any(Date('%Y-%m-%d'), Fallback(None)),
        'end': Any(Date('%Y-%m-%d'), Fallback(None)),
        Extra: Remove
        })

    params = schema(request.GET.mixed())

    if params['start']:
        enrollments_query = enrollments_query.filter(
            models.Enrollment.consent_date >= params['start'])

    if params['end']:
        enrollments_query = enrollments_query.filter(
            models.Enrollment.consent_date <= params['end'])

    if params['status']:
        enrollments_query = enrollments_query.filter(
            statuses[params['status']])

    pagination = Pagination(
        params['page'], 25, enrollments_query.count())

    enrollments = (
        enrollments_query
        .offset(pagination.offset)
        .limit(pagination.per_page)
        .all())

    def make_page_url(page):
        _query = params.copy()
        _query['page'] = page
        return request.current_route_path(_query=_query)

    return {
        'params': params,
        'total_active': (
            context.enrollments.filter(statuses['active']).count()),
        'total_terminated': (
            context.enrollments.filter(statuses['terminated']).count()),
        'total_termination_overdue': (
            context.enrollments.filter(statuses['termination_overdue'])
            .count()),
        'total_consent_overdue': (
            context.enrollments
            .join('study')
            .filter(statuses['consent_overdue'])
            .count()),
        'make_page_url': make_page_url,
        'offset_start': pagination.offset + 1,
        'offset_end': pagination.offset + len(enrollments),
        'enrollments': enrollments,
        'pagination': pagination
        }


@view_config(
    route_name='study_visits',
    permission='view',
    renderer='../templates/study/visits.pt')
def visits(context, request):
    """
    Returns overall stats about the study such as:
        * # of visits
        * # of visits by form status
        * enrollment activity
        * randomization stats
    """
    today = date.today()
    this_month_begin = date(today.year, today.month, 1)
    last_month_end = this_month_begin - timedelta(days=1)
    last_month_begin = date(last_month_end.year, last_month_end.month, 1)

    if context.is_randomized:
        arms_query = (
            Session.query(
                sa.func.coalesce(
                    models.Arm.title,
                    literal_column(_('\'(not randomized)\''))).label('title'),
                sa.func.count(models.Enrollment.id).label('enrollment_count'))
            .select_from(models.Enrollment)
            .join(models.Enrollment.study)
            .outerjoin(
                models.Stratum,
                (models.Stratum.patient_id == models.Enrollment.patient_id)
                & (models.Stratum.study_id == models.Enrollment.study_id))
            .outerjoin(models.Stratum.arm)
            .filter(models.Enrollment.study == self.study)
            .group_by(models.Arm.title)
            .order_by(models.Arm.title))
    else:
        arms_query = []

    states = Session.query(models.State).order_by('id').all()

    cycles_query = (
        Session.query(models.Cycle.name, models.Cycle.title)
        .filter_by(study=context)
        .join(models.Cycle.visits)
        .add_column(
            sa.func.count(models.Visit.id.distinct()).label('visits_count'))
        .join(
            models.Context,
            (models.Context.external == sa.sql.literal_column("'visit'"))
            & (models.Context.key == models.Visit.id))
        .join(models.Context.entity)
        .join(models.Entity.state)
        .add_columns(*[
            sa.func.count(
                sa.sql.case([
                    (models.State.name == state.name, sa.true())],
                    else_=sa.null())).label(state.name) for state in states])
        .group_by(models.Cycle.name, models.Cycle.title, models.Cycle.week)
        .order_by(models.Cycle.week.asc()))

    cycles_count = context.cycles.count()

    return {
        'arms': arms_query,
        'start_this_month': (
            context.enrollments
            .filter(models.Enrollment.consent_date >= this_month_begin)
            .count()),
        'start_last_month': (
            context.enrollments
            .filter(
                (models.Enrollment.consent_date >= last_month_begin)
                & (models.Enrollment.consent_date < this_month_begin))
            .count()),
        'end_this_month': (
            context.enrollments
            .filter(models.Enrollment.termination_date >= this_month_begin)
            .count()),
        'end_last_month': (
            context.enrollments
            .filter(
                (models.Enrollment.termination_date >= last_month_begin)
                & (models.Enrollment.termination_date < this_month_begin))
            .count()),
        'active': (
            context.enrollments
            .filter_by(termination_date=sa.null())
            .count()),
        'all_time': context.enrollments.count(),
        'states': states,
        'cycles': cycles_query,
        'cycles_count': cycles_count,
        'has_cycles': cycles_count > 0}


@view_config(
    route_name='study_visits_cycle',
    permission='view',
    renderer='../templates/study/visits_cycle.pt')
def visits_cycle(context, request):
    """
    This view displays summary statistics about visits that are related to
    this cycle, as well as a listing of those visits for reference.
    """

    page_size = 25

    cycle = (
        Session.query(models.Cycle)
        .filter_by(study=context, name=request.matchdict['cycle'])
        .first())

    if not cycle:
        raise HTTPNotFound()

    states = Session.query(models.State).order_by('id').all()

    data = {
        'states': states,
        'visit_count': cycle.visits.count(),
        'data_summary': {},
        'visits_summary': {}
        }

    by_state = (request.GET.get('by_state') or '').strip()
    by_state = next(
        (state for state in states if state.name == by_state), None)

    for state in states:
        data['visits_summary'][state.name] = (
            cycle.visits.filter(models.Visit.entities.any(state=state))
            .count())
        data['data_summary'][state.name] = (
            Session.query(models.Entity)
            .join(models.Entity.contexts)
            .join(
                models.Visit,
                (models.Context.external == 'visit')
                & (models.Visit.id == models.Context.key))
            .filter(models.Visit.cycles.any(id=cycle.id))
            .filter(models.Entity.state == state)
            .count())

    def count_state_exp(name):
        return sa.func.count(
            sa.sql.case([
                (models.State.name == name, sa.true())],
                else_=sa.null()))

    visits_query = (
        Session.query(
            models.Patient.pid,
            models.Visit.visit_date)
        .select_from(models.Visit)
        .filter(models.Visit.cycles.any(id=cycle.id))
        .join(models.Visit.patient)
        .join(
            models.Context,
            (models.Context.external == sa.sql.literal_column(u"'visit'"))
            & (models.Context.key == models.Visit.id))
        .join(models.Context.entity)
        .join(models.Entity.state)
        .add_columns(*[
            count_state_exp(state.name).label(state.name)
            for state in states])
        .group_by(
            models.Patient.pid,
            models.Visit.visit_date)
        .order_by(models.Visit.visit_date.desc()))

    if by_state:
        visits_query = visits_query.having(count_state_exp(by_state.name) > 0)

    total_visits = visits_query.count()
    total_pages = total_visits / page_size

    try:
        page = int((request.GET.get('page') or '').strip())
    except ValueError:
        page = 1
    else:
        page = max(1, min(page, total_pages))

    visits = visits_query.offset((page - 1) * page_size).limit(page_size).all()

    def make_page_url(page):
        return request.current_route_path(_query={
            'state': by_state and by_state.name,
            'page': page})

    data.update({
        'cycle': cycle,
        'by_state': by_state,
        'offset_start': max(1, (page - 1) * page_size),
        'offset_end': ((page - 1) * page_size) + len(visits),
        'total_visits': total_visits,
        'make_page_url': make_page_url,
        'pagination': Pagination(page, page_size, total_visits),
        'visits': visits
    })

    return data


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
    except Invalid as e:
        raise HTTPBadRequest(json={'errors': invalid2dict(e)})

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
    study.end_date = data['end_date']
    study.termination_schema = data['termination_form']
    study.is_locked = data['is_locked']
    study.is_randomized = data['is_randomized']

    if study.is_randomized:
        study.is_blinded = data['is_blinded']
        study.randomization_schema = data['randomization_form']
    else:
        study.is_blinded = None
        study.randomization_schema = None

    Session.flush()

    if isinstance(context, models.StudyFactory):
        request.session.flash(_(u'New study added!', 'success'))

    return view_json(study, request)


@view_config(
    route_name='studies',
    permission='add',
    xhr=True,
    request_param='vocabulary=available_termination',
    renderer='json')
@view_config(
    route_name='study',
    permission='edit',
    xhr=True,
    request_param='vocabulary=available_termination',
    renderer='json')
def available_termination(context, request):
    """
    Returns a JSON listing of avavilable schemata for terminiation
    """
    term = (request.GET.get('term') or u'').strip()

    query = (
        Session.query(models.Schema)
        .filter(models.Schema.publish_date != sa.null())
        .filter(models.Schema.retract_date == sa.null()))

    if isinstance(context, models.Study):
        query = (
            query
            .filter(~models.Schema.name.in_(
                # Filter out schemata that is already in use by the study
                Session.query(models.Schema.name)
                .select_from(models.Study)
                .filter(models.Study.id == context.id)
                .join(models.Study.schemata)
                .union(
                    # Filter out randomization schemata
                    Session.query(models.Schema.name)
                    .select_from(models.Study)
                    .join(models.Study.randomization_schema)
                    .filter(models.Study.id == context.id))
                .subquery())))

    if term:
        query = query.filter(models.Schema.title.ilike(u'%' + term + u'%'))

    query = (
        query
        .order_by(
            models.Schema.title,
            models.Schema.publish_date)
        .limit(100))

    return {'schemata': [form_views.version2json(i) for i in query]}


@view_config(
    route_name='studies',
    permission='add',
    xhr=True,
    request_param='vocabulary=available_randomization',
    renderer='json')
@view_config(
    route_name='study',
    permission='edit',
    xhr=True,
    request_param='vocabulary=available_randomization',
    renderer='json')
def available_randomization(context, request):
    """
    Returns a JSON listing of avavilable schemata for randomization
    """
    term = (request.GET.get('term') or u'').strip()

    query = (
        Session.query(models.Schema)
        .filter(models.Schema.publish_date != sa.null())
        .filter(models.Schema.retract_date == sa.null()))

    if isinstance(context, models.Study):
        query = (
            query
            .filter(~models.Schema.name.in_(
                # Filter out schemata that is already in use by the study
                Session.query(models.Schema.name)
                .select_from(models.Study)
                .filter(models.Study.id == context.id)
                .join(models.Study.schemata)
                .union(
                    # Filter out terminiation schemata
                    Session.query(models.Schema.name)
                    .select_from(models.Study)
                    .join(models.Study.termination_schema)
                    .filter(models.Study.id == context.id))
                .subquery())))

    if term:
        query = query.filter(models.Schema.title.ilike(u'%' + term + u'%'))

    query = (
        query
        .order_by(
            models.Schema.title,
            models.Schema.publish_date)
        .limit(100))

    return {'schemata': [form_views.version2json(i) for i in query]}


@view_config(
    route_name='study',
    permission='edit',
    xhr=True,
    request_param='vocabulary=available_schemata',
    renderer='json')
def available_schemata(context, request):
    """
    Returns a JSON listing of avavilable schemata for studies to use.
    """
    term = (request.GET.get('term') or u'').strip()

    InnerSchema = orm.aliased(models.Schema)
    titles_query = (
        Session.query(models.Schema.name)
        .add_column(
            Session.query(InnerSchema.title)
            .filter(InnerSchema.name == models.Schema.name)
            .filter(InnerSchema.publish_date != sa.null())
            .filter(InnerSchema.retract_date == sa.null())
            .order_by(InnerSchema.publish_date.desc())
            .limit(1)
            .correlate(models.Schema)
            .as_scalar()
            .label('title'))
        .filter(models.Schema.publish_date != sa.null())
        .filter(models.Schema.retract_date == sa.null())
        .filter(~models.Schema.name.in_(
            # Filter out schemata that is already in use by the study
            Session.query(models.Schema.name)
            .select_from(models.Study)
            .filter(models.Study.id == context.id)
            .join(models.Study.schemata)
            .union(
                # Filter out termination schemata
                Session.query(models.Schema.name)
                .select_from(models.Study)
                .join(models.Study.termination_schema)
                .filter(models.Study.id == context.id),

                # Filter out randomization schemata
                Session.query(models.Schema.name)
                .select_from(models.Study)
                .join(models.Study.randomization_schema)
                .filter(models.Study.id == context.id))
            .subquery()))
        .group_by(models.Schema.name)
        .subquery())

    query = Session.query(titles_query)

    if term:
        query = query.filter(titles_query.c.title.ilike(u'%' + term + u'%'))

    query = query.order_by(titles_query.c.title).limit(100)

    return {'schemata': [{'name': r.name, 'title': r.title} for r in query]}


@view_config(
    route_name='study',
    permission='edit',
    xhr=True,
    request_param='vocabulary=available_versions',
    renderer='json')
def available_version(context, request):
    """
    Returns a JSON listing of schemata versions for studies to use.
    """
    term = (request.GET.get('term') or u'').strip()
    schema = (request.GET.get('schema') or u'').strip()

    if not schema:
        return []

    query = (
        Session.query(models.Schema)
        .filter(models.Schema.name == schema)
        .filter(models.Schema.publish_date != sa.null())
        .filter(models.Schema.retract_date == sa.null()))

    if term:
        publish_string = sa.cast(models.Schema.publish_date, sa.String)
        query = query.filter(publish_string.ilike(u'%' + term + u'%'))

    query = query.order_by(models.Schema.publish_date.desc()).limit(100)

    return {'versions': [form_views.version2json(s) for s in query]}


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

    def check_published(value):
        if value.publish_date is None:
            raise Invalid(request.localizer.translate(
                _(u'${schema} is not published'),
                mapping={'schema': value.title}))
        return value

    def check_not_patient_schema(value):
        (exists,) = (
            Session.query(
                Session.query(models.Schema)
                .join(models.patient_schema_table)
                .filter(models.Schema.name == value.name)
                .exists())
            .one())
        if exists:
            raise Invalid(request.localizer.translate(
                _(u'${schema} is already used as a patient form'),
                mapping={'schema': value.title}))
        return value

    def check_not_randomization_schema(value):
        if (context.randomization_schema is not None
                and context.randomization_schema.name == value.name):
            raise Invalid(request.localizer.translate(
                _(u'${schema} is already used as a randomization form'),
                mapping={'schema': value.title}))
        return value

    def check_not_termination_schema(value):
        if (context.termination_schema is not None
                and context.termination_schema.name == value.name):
            raise Invalid(request.localizer.translate(
                _(u'${schema} is already used as a termination form'),
                mapping={'schema': value.title}))
        return value

    def check_same_schema(value):
        versions = value['versions']
        schema = value['schema']
        invalid = [i.publish_date for i in versions if i.name != schema]
        if invalid:
            raise Invalid(request.localizer(
                _(u'Incorrect version: ${versions}'),
                mapping={'versions': ', '.join(map(str, invalid))}),
                path=['versions'])
        return value

    schema = Schema(All({
        'schema': All(Type(*six.string_types), Coerce(six.binary_type)),
        'versions': [All(
            int,
            Model(models.Schema, localizer=request.localizer),
            check_published,
            check_not_patient_schema,
            check_not_randomization_schema,
            check_not_termination_schema,
            )],
        Extra: Remove},
        check_same_schema,
        ))

    try:
        data = schema(request.json_body)
    except Invalid as e:
        raise HTTPBadRequest(json={'errors': invalid2dict(e)})

    old_items = set(i for i in context.schemata if i.name == data['schema'])
    new_items = set(data['versions'])

    # Remove unselected
    context.schemata.difference_update(old_items - new_items)

    # Add newly selected
    context.schemata.update(new_items)

    # Get a list of cycles to update
    cycles = (
        Session.query(models.Cycle)
        .options(orm.joinedload(models.Cycle.schemata))
        .filter(models.Cycle.study == context)
        .filter(models.Cycle.schemata.any(name=data['schema'])))

    # Also update available cycle schemata versions
    for cycle in cycles:
        cycle.schemata.difference_update(old_item - new_items)
        cycle.schemata.update(new_items)

    return form_views.form2json(new_items)[0]


@view_config(
    route_name='study_schema',
    permission='edit',
    request_method='DELETE',
    xhr=True,
    renderer='json')
def delete_schema_json(context, request):
    check_csrf_token(request)
    schema_name = request.matchdict.get('schema')

    if not schema_name:
        raise HTTPBadRequest()

    (exists,) = (
        Session.query(
            Session.query(models.Study)
            .filter(models.Study.schemata.any(name=schema_name))
            .filter(models.Study.id == context.id)
            .exists())
        .one())

    if not exists:
        raise HTTPNotFound()

    # Remove from cycles
    Session.execute(
        models.cycle_schema_table.delete()
        .where(
            models.cycle_schema_table.c.cycle_id.in_(
                Session.query(models.Cycle.id)
                .filter_by(study=context)
                .subquery())
            & models.cycle_schema_table.c.schema_id.in_(
                Session.query(models.Schema.id)
                .filter_by(name=schema_name)
                .subquery())))

    # Remove from study
    Session.execute(
        models.study_schema_table.delete()
        .where(
            (models.study_schema_table.c.study_id == context.id)
            & (models.study_schema_table.c.schema_id.in_(
                Session.query(models.Schema.id)
                .filter_by(name=schema_name)
                .subquery()))))

    mark_changed(Session())

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
    """
    Enables/Disables a form for a cycle

    Request body json parameters:
        schema -- name of the schema (will used study-enabled versions)
        cycle -- cycle id
        enabled -- true/false
    """
    check_csrf_token(request)

    def check_schema_in_study(value):
        (exists,) = (
            Session.query(
                Session.query(models.Study)
                .filter(models.Study.cycles.any(study_id=context.id))
                .filter(models.Study.schemata.any(name=value))
                .exists())
            .one())
        if not exists:
            msg = _('${study} does not have form "${schema}"')
            mapping = {'schema': value, 'study': context.title}
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
            Coerce(six.binary_type),
            check_schema_in_study),
        'cycle': All(
            Model(models.Cycle, localizer=request.localizer),
            check_cycle_in_study),
        'enabled': Boolean(),
        Extra: Remove
        })

    try:
        data = schema(request.json_body)
    except Invalid as e:
        raise HTTPBadRequest(json={'errors': invalid2dict(e)})

    schema_name = data['schema']
    cycle = data['cycle']
    enabled = data['enabled']

    study_items = set(i for i in context.schemata if i.name == schema_name)
    cycle_items = set(i for i in cycle.schemata if i.name == schema_name)

    if enabled:
        # Match cycle schemata to the study's schemata for the given name
        cycle.schemata.difference_update(cycle_items - study_items)
        cycle.schemata.update(study_items)
    else:
        cycle.schemata.difference_update(study_items | cycle_items)

    return HTTPOk()


@view_config(
    route_name='study',
    xhr=True,
    permission='edit',
    request_method='POST',
    request_param='upload',
    renderer='json')
def upload_randomization(context, request):
    """
    Handles RANDID file uploads.
    The file is expected to be a CSV with the following columns:
        * ARM
        * STRATA
        * BLOCKID
        * RANDID
    In addition, the CSV file must have the columns as the form
    it is using for randomization.
    """

    check_csrf_token(request)

    if not context.is_randomized:
        raise HTTPBadRequest(body=_(u'This study is not randomized'))

    if not context.randomization_schema:
        raise HTTPBadRequest(
            body=_(u'This study has no randomization form configured'))

    if mimetypes.guess_type(request.POST['upload'].filename)[0] != 'text/csv':
        raise HTTPBadRequest(body=_(u'Invalid file-type, must be CSV'))

    arms = dict([(arm.name, arm) for arm in context.arms])

    # Default to comple state since they're generated by a statistician
    complete = Session.query(models.State).filter_by(name=u'complete').one()

    input_file = request.POST['upload'].file
    input_file.seek(0)

    reader = csv.DictReader(input_file)

    missing = [field_name
               for field_name in study.randomization_schema.keys()
               if k not in reader.fieldnames]

    if missing:
        raise HTTPBadRequest(body=_(
            u'File upload is missing the following columns ${columns}',
            mapping={'columns': ', '.join(missing)}))

    for row in reader:
        if row['ARM'] not in arms:
            arms[row['ARM']] = models.Arm(
                study=context,
                name=row['ARM'],
                title=row['ARM'])

        stratum = models.Stratum(
            study=context,
            arm=arms[row['ARM']],
            label=row.get('STRATA'),
            block_number=int(row['BLOCKID']),
            randid=row['RANDID'])

        Session.add(stratum)

        entity = models.Entity(
            schema=context.randomization_schema,
            state=complete)

        for field_name in study.randomization_schema.keys():
            entity[field_name] = row[field_name.upper()]

        stratum.entities.add(entity_entry)

    try:
        Session.flush()
    except sa.exc.IntegrityError as e:
        if 'uq_stratum_reference_number' in e.message:
            raise HTTPBadRequest(body=_(
                u'The submitted file contains existing reference numbers. '
                u'Please upload a file with new reference numbers.'))

    return HTTPOk()


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
            Type(*six.string_types),
            Coerce(six.binary_type),
            Length(min=3, max=32),
            Match(r'^[a-z0-9_\-]+$'),
            check_unique_name),
        'title': All(
            Type(*six.string_types),
            Coerce(six.text_type),
            Length(min=3, max=32)),
        'code': All(
            Type(*six.string_types),
            Coerce(six.binary_type),
            Length(min=3, max=8)),
        'short_title': All(
            Type(*six.string_types),
            Coerce(six.text_type),
            Length(min=3, max=8)),
        'consent_date': Date('%Y-%m-%d'),
        'start_date': Any(Date('%Y-%m-%d'), Default(None)),
        'end_date':  Any(Date('%Y-%m-%d'), Default(None)),
        'is_locked': Any(Boolean(), Default(False)),
        'termination_form': Any(
            All(int, Model(models.Schema, localizer=request.localizer)),
            Default(None)),
        'is_randomized': Any(Boolean(), Default(False)),
        'is_blinded': Any(Boolean(), Default(False)),
        'randomization_form': Any(
            All(int, Model(models.Schema, localizer=request.localizer)),
            Default(None)),
        Extra: Remove})
