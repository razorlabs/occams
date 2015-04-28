try:
    import unicodecsv as csv
except ImportError:  # pragma: nocover
    import csv
from datetime import date, timedelta

from slugify import slugify
from pyramid.events import subscriber, BeforeRender
from pyramid.httpexceptions import \
    HTTPBadRequest, HTTPForbidden, HTTPNotFound, HTTPOk
from pyramid.session import check_csrf_token
from pyramid.view import view_config
import sqlalchemy as sa
from sqlalchemy import orm
import wtforms
from wtforms.ext.dateutil.fields import DateField
from zope.sqlalchemy import mark_changed

from occams.utils.forms import wtferrors, ModelField
from occams.utils.pagination import Pagination
from occams_forms.renderers import form2json, version2json

from .. import _, models, Session
from . import cycle as cycle_views


@subscriber(BeforeRender)
def add_studies(event):
    """
    Inject studies listing into Chameleon template variables to render menu.
    """
    if event['renderer_info'].type != '.pt':
        return
    studies_query = Session.query(models.Study).order_by(models.Study.title)
    event.rendering_val['available_studies'] = studies_query.all()


@view_config(
    route_name='studies.main',
    permission='view',
    renderer='../templates/study/list.pt')
def list_(request):
    studies_query = (
        Session.query(models.Study)
        .order_by(models.Study.title.asc()))

    sites_query = Session.query(models.Site)
    site_ids = [s.id for s in sites_query if request.has_permission('view', s)]

    if not site_ids:
        modified_query = []
        modified_count = 0

    else:

        modified_query = (
            Session.query(models.Patient)
            .filter(models.Patient.site.has(models.Site.id.in_(site_ids)))
            .order_by(models.Patient.modify_date.desc())
            .limit(10))

        modified_count = modified_query.count()

    viewed = sorted((request.session.get('viewed') or {}).values(),
                    key=lambda v: v['view_date'],
                    reverse=True)

    studies_data = [view_json(s, request, deep=False) for s in studies_query]

    return {
        'studies_data': studies_data,
        'studies_count': len(studies_data),

        'modified': modified_query,
        'modified_count': modified_count,

        'viewed': viewed,
        'viewed_count': len(viewed),
    }


@view_config(
    route_name='studies.study',
    permission='view',
    renderer='../templates/study/view.pt')
def view(context, request):
    return {'study': view_json(context, request)}


@view_config(
    route_name='studies.study',
    permission='view',
    xhr=True,
    renderer='json')
def view_json(context, request, deep=True):
    study = context
    data = {
        '__url__': request.route_path('studies.study', study=study.name),
        'id': study.id,
        'name': study.name,
        'title': study.title,
        'code': study.code,
        'short_title': study.short_title,
        'consent_date': study.consent_date.isoformat(),
        'start_date': study.start_date and study.start_date.isoformat(),
        'end_date': study.end_date and study.end_date.isoformat(),
        'reference_pattern': study.reference_pattern,
        'reference_hint': study.reference_hint,
        'is_randomized': study.is_randomized,
        'is_blinded': study.is_blinded,
        'termination_form':
            study.termination_schema
            and form2json(study.termination_schema),
        'randomization_form':
            study.randomization_schema
            and form2json(study.randomization_schema),
        }

    if deep:
        data.update({
            'cycles': [
                cycle_views.view_json(cycle, request)
                for cycle in study.cycles],
            'forms': form2json(study.schemata)})

    return data


@view_config(
    route_name='studies.study_enrollments',
    permission='view',
    renderer='../templates/study/enrollments.pt')
def enrollments(context, request):
    """
    Displays enrollment summary and allows the user to filter by date.
    """

    statuses = {
        'active': models.Enrollment.termination_date == sa.null(),
        'terminated': models.Enrollment.termination_date != sa.null(),
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

    class FilterForm(wtforms.Form):
        page = wtforms.IntegerField()
        status = wtforms.StringField(
            validators=[
                wtforms.validators.Optional(),
                wtforms.validators.AnyOf(statuses)])
        start = DateField()
        end = DateField()

    form = FilterForm(request.GET)
    form.validate()

    if form.start.data:
        enrollments_query = enrollments_query.filter(
            models.Enrollment.consent_date >= form.start.data)

    if form.end.data:
        enrollments_query = enrollments_query.filter(
            models.Enrollment.consent_date <= form.end.data)

    if form.status.data:
        enrollments_query = enrollments_query.filter(
            statuses[form.status.data])

    pagination = Pagination(
        form.page.data, 25, enrollments_query.count())

    enrollments = (
        enrollments_query
        .offset(pagination.offset)
        .limit(pagination.per_page)
        .all())

    def make_page_url(page):
        _query = form.data
        _query['page'] = page
        return request.current_route_path(_query=_query)

    return {
        'params': form.data,
        'total_active': (
            context.enrollments.filter(statuses['active']).count()),
        'total_terminated': (
            context.enrollments.filter(statuses['terminated']).count()),
        'make_page_url': make_page_url,
        'offset_start': pagination.offset + 1,
        'offset_end': pagination.offset + len(enrollments),
        'enrollments': enrollments,
        'pagination': pagination
        }


@view_config(
    route_name='studies.study_visits',
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
                    sa.literal_column(_('\'(not randomized)\''))
                    ).label('title'),
                sa.func.count(models.Enrollment.id).label('enrollment_count'))
            .select_from(models.Enrollment)
            .join(models.Enrollment.study)
            .outerjoin(
                models.Stratum,
                (models.Stratum.patient_id == models.Enrollment.patient_id)
                & (models.Stratum.study_id == models.Enrollment.study_id))
            .outerjoin(models.Stratum.arm)
            .filter(models.Enrollment.study == context)
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
    route_name='studies.study_visits_cycle',
    permission='view',
    renderer='../templates/study/visits_cycle.pt')
def visits_cycle(context, request):
    """
    This view displays summary statistics about visits that are related to
    this cycle, as well as a listing of those visits for reference.
    """

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

    try:
        page = int((request.GET.get('page') or '').strip())
    except ValueError:
        page = 1

    pagination = Pagination(page, 25, total_visits)

    visits = (
        visits_query
        .offset(pagination.offset)
        .limit(pagination.per_page)
        .all())

    def make_page_url(page):
        return request.current_route_path(_query={
            'state': by_state and by_state.name,
            'page': page})

    data.update({
        'cycle': cycle,
        'by_state': by_state,
        'offset_start': pagination.offset + 1,
        'offset_end': pagination.offset + len(visits),
        'total_visits': total_visits,
        'make_page_url': make_page_url,
        'pagination': pagination,
        'visits': visits
    })

    return data


@view_config(
    route_name='studies.main',
    permission='add',
    request_method='POST',
    xhr=True,
    renderer='json')
@view_config(
    route_name='studies.study',
    permission='edit',
    request_method='PUT',
    xhr=True,
    renderer='json')
def edit_json(context, request):
    check_csrf_token(request)

    form = StudySchema(context, request).from_json(request.json_body)

    if not form.validate():
        raise HTTPBadRequest(json={'errors': wtferrors(form)})

    if isinstance(context, models.StudyFactory):
        study = models.Study()
        Session.add(study)
    else:
        study = context

    study.name = slugify(form.title.data)
    study.title = form.title.data
    study.code = form.code.data
    study.short_title = form.short_title.data
    study.consent_date = form.consent_date.data
    study.start_date = form.start_date.data
    study.termination_schema = form.termination_form.data
    study.is_randomized = form.is_randomized.data
    study.is_blinded = \
        None if not study.is_randomized else form.is_blinded.data
    study.randomization_schema = \
        None if not study.is_randomized else form.randomization_form.data

    Session.flush()

    return view_json(study, request)


@view_config(
    route_name='studies.main',
    permission='edit',
    xhr=True,
    request_param='vocabulary=available_schemata',
    renderer='json')
@view_config(
    route_name='studies.study',
    permission='edit',
    xhr=True,
    request_param='vocabulary=available_schemata',
    renderer='json')
def available_schemata(context, request):
    """
    Returns a listing of available schemata for the study

    The results will try to exclude schemata configured for patients,
    or schemata that is currently used by the context study (if editing).

    GET parameters:
        term -- (optional) filters by schema title or publish date
        schema -- (optional) only shows results for specific schema name
                  (useful for searching for a schema's publish dates)
        grouped -- (optional) groups all results by schema name
    """

    class SearchForm(wtforms.Form):
        term = wtforms.StringField()
        schema = wtforms.StringField()
        grouped = wtforms.BooleanField()

    form = SearchForm(request.GET)
    form.validate()

    query = (
        Session.query(models.Schema)
        .filter(models.Schema.publish_date != sa.null())
        .filter(models.Schema.retract_date == sa.null())
        .filter(~models.Schema.name.in_(
            # Exclude patient schemata
            Session.query(models.Schema.name)
            .join(models.patient_schema_table)
            .subquery())))

    if form.schema.data:
        query = query.filter(models.Schema.name == form.schema.data)

    if form.term.data:
        wildcard = u'%' + form.term.data + u'%'
        query = query.filter(
            models.Schema.title.ilike(wildcard)
            | sa.cast(models.Schema.publish_date, sa.Unicode).ilike(wildcard))

    if isinstance(context, models.Study):

        # Filter out schemata that is already in use by the study

        if context.randomization_schema:
            query = query.filter(
                models.Schema.name != context.randomization_schema.name)

        if context.termination_schema:
            query = query.filter(
                models.Schema.name != context.termination_schema.name)

        query = query.filter(~models.Schema.name.in_(
            Session.query(models.Schema.name)
            .select_from(models.Study)
            .filter(models.Study.id == context.id)
            .join(models.Study.schemata)
            .subquery()))

    query = (
        query.order_by(
            models.Schema.title,
            models.Schema.publish_date.asc())
        .limit(100))

    return {
        '__query__': form.data,
        'schemata': (form2json(query)
                     if form.grouped.data
                     else [version2json(i) for i in query])
    }


@view_config(
    route_name='studies.study',
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

    msg = _(u'Successfully deleted ${study}',
            mapping={'study': context.title})
    request.session.flash(msg, 'success')

    return {'__next__': request.route_path('studies.main')}


@view_config(
    route_name='studies.study_schemata',
    permission='edit',
    request_method='POST',
    xhr=True,
    renderer='json')
def add_schema_json(context, request):
    check_csrf_token(request)

    def check_not_patient_schema(form, field):
        (exists,) = (
            Session.query(
                Session.query(models.Schema)
                .join(models.patient_schema_table)
                .filter(models.Schema.name == field.data)
                .exists())
            .one())
        if exists:
            raise wtforms.ValidationError(request.localizer.translate(
                _(u'Already a patient form')))

    def check_not_randomization_schema(form, field):
        if (context.randomization_schema
                and context.randomization_schema.name == field.data):
            raise wtforms.ValidationError(request.localizer.translate(
                _(u'Already a randomization form')))

    def check_not_termination_schema(form, field):
        if (context.termination_schema is not None
                and context.termination_schema.name == field.data):
            raise wtforms.ValidationError(request.localizer.translate(
                _(u'Already a termination form')))

    def check_same_schema(form, field):
        versions = form.versions.data
        schema = form.schema.data
        invalid = [i.publish_date for i in versions if i.name != schema]
        if invalid:
            raise wtforms.ValidationError(request.localizer.translate(_(
                _(u'Incorrect versions: ${versions}'),
                mapping={'versions': ', '.join(map(str, invalid))})))

    def check_published(form, field):
        if field.data.publish_date is None:
            raise wtforms.ValidationError(request.localizer.translate(
                _(u'Selected version is not published')))

    class SchemaManagementForm(wtforms.Form):
        schema = wtforms.StringField(
            validators=[
                wtforms.validators.InputRequired(),
                check_not_patient_schema,
                check_not_randomization_schema,
                check_not_termination_schema])
        versions = wtforms.FieldList(
            ModelField(
                session=Session,
                class_=models.Schema,
                validators=[
                    wtforms.validators.InputRequired(),
                    check_published]),
            validators=[check_same_schema],
            min_entries=1)

    form = SchemaManagementForm.from_json(request.json_body)

    if not form.validate():
        raise HTTPBadRequest(json={'errors': wtferrors(form)})

    old_items = set(i for i in context.schemata if i.name == form.schema.data)
    new_items = set(form.versions.data)

    # Remove unselected
    context.schemata.difference_update(old_items - new_items)

    # Add newly selected
    context.schemata.update(new_items)

    # Get a list of cycles to update
    cycles = (
        Session.query(models.Cycle)
        .options(orm.joinedload(models.Cycle.schemata))
        .filter(models.Cycle.study == context)
        .filter(models.Cycle.schemata.any(name=form.schema.data)))

    # Also update available cycle schemata versions
    for cycle in cycles:
        cycle.schemata.difference_update(old_items - new_items)
        cycle.schemata.update(new_items)

    return form2json(new_items)[0]


@view_config(
    route_name='studies.study_schema',
    permission='edit',
    request_method='DELETE',
    xhr=True,
    renderer='json')
def delete_schema_json(context, request):
    check_csrf_token(request)
    schema_name = request.matchdict.get('schema')

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
    route_name='studies.study_schedule',
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

    def check_cycle_association(form, field):
        if field.data.study != context:
            raise wtforms.ValidationError(request.localizer.translate(_(
                u'Not a valid choice')))

    def check_form_association(form, field):
        query = (
            Session.query(models.Schema)
            .join(models.study_schema_table)
            .filter(models.Schema.name == field.data)
            .filter(models.study_schema_table.c.study_id == context.id))
        (exists,) = Session.query(query.exists()).one()
        if not exists:
            raise wtforms.ValidationError(request.localizer.translate(_(
                u'Not a valid choice')))

    class ScheduleForm(wtforms.Form):
        schema = wtforms.StringField(
            validators=[
                wtforms.validators.InputRequired(),
                check_form_association])
        cycle = ModelField(
            session=Session,
            class_=models.Cycle,
            validators=[
                wtforms.validators.InputRequired(),
                check_cycle_association])
        enabled = wtforms.BooleanField()

    form = ScheduleForm.from_json(request.json_body)

    if not form.validate():
        raise HTTPBadRequest(json={'errors': wtferrors(form)})

    schema_name = form.schema.data
    cycle = form.cycle.data
    enabled = form.enabled.data

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
    route_name='studies.study',
    xhr=True,
    permission='edit',
    request_method='POST',
    request_param='upload',
    renderer='json')
def upload_randomization_json(context, request):
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
        # No form check required as its checked via database constraint
        raise HTTPBadRequest(body=_(u'This study is not randomized'))

    input_file = request.POST['upload'].file
    input_file.seek(0)

    # Ensure we can read the CSV
    try:
        csv.Sniffer().sniff(input_file.read(1024))
    except csv.Error:
        raise HTTPBadRequest(body=_(u'Invalid file-type, must be CSV'))
    else:
        input_file.seek(0)

    reader = csv.DictReader(input_file)

    # Case-insensitive lookup
    fieldnames = dict((name.upper(), name) for name in reader.fieldnames)
    stratumkeys = ['ARM', 'BLOCKID', 'RANDID']
    formkeys = context.randomization_schema.attributes.keys()

    # Ensure the CSV defines all required columns
    required = stratumkeys + formkeys
    missing = [name for name in required if name.upper() not in fieldnames]
    if missing:
        raise HTTPBadRequest(body=_(
            u'File upload is missing the following columns ${columns}',
            mapping={'columns': ', '.join(missing)}))

    # We'll be using this to create new arms as needed
    arms = dict([(arm.name, arm) for arm in context.arms])

    # Default to comple state since they're generated by a statistician
    complete = Session.query(models.State).filter_by(name=u'complete').one()

    for row in reader:
        arm_name = row[fieldnames['ARM']]
        if arm_name not in arms:
            arms[arm_name] = models.Arm(
                study=context, name=arm_name, title=arm_name)

        stratum = models.Stratum(
            study=context,
            arm=arms[arm_name],
            block_number=int(row[fieldnames['BLOCKID']]),
            randid=row[fieldnames['RANDID']])

        if 'STRATA' in fieldnames:
            stratum.label = row[fieldnames['STRATA']]

        Session.add(stratum)

        entity = models.Entity(
            schema=context.randomization_schema, state=complete)

        for key in formkeys:
            entity[key] = row[fieldnames[key.upper()]]

        stratum.entities.add(entity)

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

    def check_unique_url(form, field):
        slug = slugify(field.data)
        query = Session.query(models.Study).filter_by(name=slug)
        if isinstance(context, models.Study):
            query = query.filter(models.Study.id != context.id)
        (exists,) = Session.query(query.exists()).one()
        if exists:
            raise wtforms.ValidationError(request.localizer.translate(_(
                u'Does not yield a unique URL.')))

    class StudyForm(wtforms.Form):
        title = wtforms.StringField(
            validators=[
                wtforms.validators.InputRequired(),
                wtforms.validators.Length(min=3, max=32),
                check_unique_url])
        code = wtforms.StringField(
            validators=[
                wtforms.validators.InputRequired(),
                wtforms.validators.Length(min=3, max=8)])
        short_title = wtforms.StringField(
            validators=[
                wtforms.validators.InputRequired(),
                wtforms.validators.Length(min=3, max=8)])
        consent_date = DateField()
        start_date = DateField()
        termination_form = ModelField(
            session=Session,
            class_=models.Schema)
        is_randomized = wtforms.BooleanField()
        is_blinded = wtforms.BooleanField()
        randomzation_form = ModelField(
            session=Session,
            class_=models.Schema)

    return StudyForm
