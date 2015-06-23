from datetime import datetime, date

from pyramid.httpexceptions import HTTPBadRequest, HTTPOk, HTTPNotFound
from pyramid.renderers import render
from pyramid.session import check_csrf_token
from pyramid.view import view_config
import sqlalchemy as sa
from sqlalchemy import orm
import wtforms
from wtforms.ext.dateutil.fields import DateField

from occams.utils.forms import wtferrors, ModelField, Form
from occams_forms.renderers import \
    make_form, render_form, apply_data, entity_data, modes
from occams_datastore.reporting import build_report

from .. import _, log, models, Session


@view_config(
    route_name='studies.enrollments',
    permission='view',
    xhr=True,
    renderer='json')
def list_json(context, request):
    patient = context.__parent__
    enrollments_query = (
        Session.query(models.Enrollment)
        .filter_by(patient=patient)
        .options(
            orm.joinedload('patient').joinedload('site'),
            orm.joinedload('study'),
            orm.joinedload('stratum').joinedload('arm'))
        .order_by(models.Enrollment.consent_date.desc()))

    return {
        'enrollments': [view_json(e, request) for e in enrollments_query]
        }


@view_config(
    route_name='studies.enrollment',
    permission='view',
    xhr=True,
    renderer='json')
def view_json(context, request):
    enrollment = context
    study = context.study
    patient = context.patient
    can_randomize = bool(request.has_permission('randomize', context))
    return {
        '__url__': request.route_path(
            'studies.enrollment',
            patient=patient.pid,
            enrollment=enrollment.id),
        '__randomization_url__': request.route_path(
            'studies.enrollment_randomization',
            patient=patient.pid,
            enrollment=enrollment.id),
        '__termination_url__': request.route_path(
            'studies.enrollment_termination',
            patient=patient.pid,
            enrollment=enrollment.id),
        '__can_edit__':
            bool(request.has_permission('edit', context)),
        '__can_terminate__':
            bool(request.has_permission('terminate', context))
            and bool(study.termination_schema),
        '__can_randomize__': can_randomize,
        '__can_delete__':
            bool(request.has_permission('delete', context)),
        'id': enrollment.id,
        'study': {
            'id': study.id,
            'name': study.name,
            'title': study.title,
            'is_randomized': study.is_randomized,
            'is_blinded': study.is_blinded,
            'start_date': study.start_date.isoformat(),
            },
        'stratum':
            None if not (study.is_randomized and enrollment.stratum) else {
                'id': enrollment.stratum.id,
                'arm': None if study.is_blinded or not can_randomize else {
                    'id': enrollment.stratum.arm.id,
                    'name': enrollment.stratum.arm.name,
                    'title': enrollment.stratum.arm.title,
                },
                'randid':
                    enrollment.stratum.randid if not study.is_blinded else None
                },
        'consent_date': enrollment.consent_date.isoformat(),
        'latest_consent_date': enrollment.latest_consent_date.isoformat(),
        'termination_date': (
            enrollment.termination_date
            and enrollment.termination_date.isoformat()),
        'reference_number': enrollment.reference_number,
        }


@view_config(
    route_name='studies.enrollments',
    permission='add',
    xhr=True,
    request_method='POST',
    renderer='json')
@view_config(
    route_name='studies.enrollment',
    permission='edit',
    xhr=True,
    request_method='PUT',
    renderer='json')
def edit_json(context, request):
    check_csrf_token(request)

    form = EnrollmentSchema(context, request).from_json(request.json_body)

    if not form.validate():
        raise HTTPBadRequest(json={'errors': wtferrors(form)})

    if isinstance(context, models.EnrollmentFactory):
        enrollment = models.Enrollment(
            patient=context.__parent__, study=form.study.data)
    else:
        enrollment = context

    enrollment.patient.modify_date = datetime.now()
    enrollment.consent_date = form.consent_date.data
    enrollment.latest_consent_date = form.latest_consent_date.data

    if not form.study.data.termination_schema:
        enrollment.termination_date = form.termination_date.data

    Session.flush()
    return view_json(enrollment, request)


@view_config(
    route_name='studies.enrollment',
    permission='delete',
    request_method='DELETE',
    xhr=True,
    renderer='json')
def delete_json(context, request):
    list(map(Session.delete, context.entities))
    context.patient.modify_date = datetime.now()
    Session.delete(context)
    Session.flush()
    request.session.flash(_(u'Deleted sucessfully'))
    return {'__next__': request.route_path('studies.patient',
                                           patient=context.patient.pid)}


@view_config(
    route_name='studies.enrollment_termination',
    permission='terminate',
    xhr=True,
    renderer='string')
def terminate_ajax(context, request):
    try:
        entity = (
            Session.query(models.Entity)
            .join(models.Entity.schema)
            .filter(models.Schema.name.in_(
                # Only search for forms being used as temrination forms
                Session.query(models.Schema.name)
                .join(models.Study.termination_schema)
                .subquery()))
            .join(models.Context)
            .filter_by(external='enrollment', key=context.id)
            .one())
    except orm.exc.MultipleResultsFound:
        raise Exception('Should only have one...')
    except orm.exc.NoResultFound:
        schema = context.study.termination_schema
        entity = models.Entity(schema=schema)
        # XXX: This is really bad form as we're applying
        # side-effects to a GET request, but there is no time
        # to make this look prety...
        # If you remove this line you will be creating random termination
        # entries...
        context.entities.add(entity)
    else:
        schema = entity.schema

    if not entity.state:
        entity.state = (
            Session.query(models.State)
            .filter_by(name='pending-entry')
            .one())

    if 'termination_date' not in schema.attributes:
        msg = 'There is no "termination_date" configured on: {}'
        log.warn(msg.format(schema.name))

    if request.has_permission('admin'):
        transition = modes.ALL
    elif request.has_permission('transition'):
        transition = modes.AVAILABLE
    else:
        transition = modes.AUTO

    Form = make_form(Session, schema, entity=entity, transition=transition, show_metadata=False)
    form = Form(request.POST, data=entity_data(entity))

    if request.method == 'POST':
        check_csrf_token(request)
        if form.validate():
            if not entity.id:
                # changing termination version *should* not be
                # allowed, just assign the schema that's already being used
                context.entities.add(entity)
            upload_dir = request.registry.settings['studies.blob.dir']
            apply_data(Session, entity, form.data, upload_dir)
            context.termination_date = form.termination_date.data
            Session.flush()
            return HTTPOk(json=view_json(context, request))
        else:
            return HTTPBadRequest(json={'errors': wtferrors(form)})

    return render_form(
        form,
        cancel_url=request.current_route_path(_route_name='studies.patient'),
        attr={
            'method': 'POST',
            'action': request.current_route_path(),
            'role': 'form',
            'data-bind': 'formentry: {}, submit: $root.terminateEnrollment'
        }
    )


def _get_randomization_form(context, request):
    try:
        entity = (
            Session.query(models.Entity)
            .join(models.Entity.contexts)
            .filter_by(external='stratum', key=context.stratum.id)
            .one())
    except orm.exc.MultipleResultsFound:
        raise Exception('Should only have one...')
    except orm.exc.NoResultFound:
        raise HTTPNotFound()
    else:
        Form = make_form(Session, entity.schema, show_metadata=False)
        form = Form(data=entity_data(entity))
    return form


def _make_challenge_form(context, request):
    if context.reference_number:
        identifier_name = _(u'study number')
    else:
        identifier_name = _(u'PID')

    def check_identifier(form, field):
        study_id = context.reference_number
        pid = context.patient.pid
        data = field.data
        if (study_id and study_id != data) \
                or (not study_id and pid != data):
            field.data = None
            raise wtforms.ValidationError(request.localizer.translate(
                u"""
                The ${identifier_name} you entered does not match this
                patient\'s ${identifier_name}.
                """,
                mapping={'identifier_name': identifier_name}))

    class ChallengeForm(Form):
        confirm = wtforms.StringField(
            _(u'You are about to randomize this patient'),
            description=request.localizer.translate(_(
                u"""
                Have you made sure that you have followed all study
                prerequisites?
                If so, please verify the patient\'s ${identifier_name}.
                """,
                mapping={'identifier_name': identifier_name})),
            validators=[
                wtforms.validators.InputRequired(),
                check_identifier])

    return ChallengeForm


@view_config(
    route_name='studies.enrollment_randomization',
    permission='randomize',
    renderer='../templates/enrollment/randomize-print.pt')
def randomize_print(context, request):
    form = _get_randomization_form(context, request)
    return {'form': render_form(form, disabled=True)}


@view_config(
    route_name='studies.enrollment_randomization',
    permission='randomize',
    xhr=True,
    renderer='json')
def randomize_ajax(context, request):

    STAGE_KEY = 'randomization_stage'
    DATA_KEY = 'randomization_data'
    CHALLENGE, ENTER, VERIFY, COMPLETE = range(4)

    is_randomized = bool(context.stratum)
    randomization_schema = context.study.randomization_schema
    error_message = None

    # Reset randomization process if not posting data
    if request.method != 'POST':
        request.session[STAGE_KEY] = CHALLENGE
        request.session[DATA_KEY] = {}

    else:
        # Validate
        check_csrf_token(request)
        if is_randomized:
            raise HTTPBadRequest(
                body=_(u'This patient is already randomized for this study'))
        if request.session.get(STAGE_KEY) in (ENTER, VERIFY):
            Form = make_form(
                Session, randomization_schema, show_metadata=False)
        else:
            Form = _make_challenge_form(context, request)
        form = Form(request.POST)
        if not form.validate():
            raise HTTPBadRequest(json={'errors': wtferrors(form)})

        # Determine next state
        if request.session.get(STAGE_KEY) == ENTER:
            request.session[STAGE_KEY] = VERIFY
            request.session[DATA_KEY] = form.data
        elif request.session[STAGE_KEY] == VERIFY:
            previous_data = request.session.get(DATA_KEY) or {}
            # ensure entered values match previous values
            for field, value in previous_data.items():
                if value != form.data.get(field):
                    # start over
                    request.session[STAGE_KEY] = ENTER
                    request.session[DATA_KEY] = None
                    error_message = _(
                        u'Your responses do not match previously entered '
                        u'responses. '
                        u'You will need to reenter your responses.')
                    break
            else:
                request.session[STAGE_KEY] = COMPLETE
        else:
            request.session[STAGE_KEY] = ENTER

        # Determine if the workflow should finish
        if request.session[STAGE_KEY] == COMPLETE:
            report = build_report(Session, randomization_schema.name)
            data = form.data

            # Get an unassigned entity that matches the input criteria
            query = (
                Session.query(models.Stratum)
                .filter(models.Stratum.study == context.study)
                .filter(models.Stratum.patient == sa.null())
                .join(models.Stratum.contexts)
                .join(models.Context.entity)
                .add_entity(models.Entity)
                .join(report, report.c.id == models.Entity.id)
                .filter(sa.and_(
                    *[(getattr(report.c, k) == v) for k, v in data.items()]))
                .order_by(models.Stratum.id.asc())
                .limit(1))

            try:
                (stratum, entity) = query.one()
            except orm.exc.NoResultFound:
                raise HTTPBadRequest(
                    body=_(u'No more stratification numbers available!'))

            # so far so good, set the contexts and complete the request
            is_randomized = True
            stratum.patient = context.patient
            entity.state = (
                Session.query(models.State).filter_by(name=u'complete').one())
            entity.collect_date = date.today()
            context.patient.entities.add(entity)
            context.entities.add(entity)
            Session.flush()
            Session.refresh(context)

    # Choose next form to render for data entry
    if is_randomized:
        template = '../templates/enrollment/randomize-view.pt'
        form = _get_randomization_form(context, request)
    elif request.session.get(STAGE_KEY) == ENTER:
        template = '../templates/enrollment/randomize-enter.pt'
        Form = make_form(Session, randomization_schema, show_metadata=False)
        form = Form()
    elif request.session.get(STAGE_KEY) == VERIFY:
        template = '../templates/enrollment/randomize-verify.pt'
        Form = make_form(Session, randomization_schema, show_metadata=False)
        form = Form()
    else:
        template = '../templates/enrollment/randomize-challenge.pt'
        Form = _make_challenge_form(context, request)
        form = Form()
        form.meta.entity = None
        form.meta.schema = randomization_schema


    return {
        'is_randomized': is_randomized,
        'enrollment': view_json(context, request),
        'content': render(template, {
            'error': error_message,
            'context': context,
            'request': request,
            'form': render_form(
                form,
                disabled=is_randomized,
                save_btn=False,
                attr={
                    'id': 'enrollment-randomization',
                    'method': 'POST',
                    'role': 'form',
                    'data-bind':
                        'formentry: {}, submit: $root.randomizeEnrollment'
                })
        })
    }


def EnrollmentSchema(context, request):

    def check_cannot_edit_study(form, field):
        is_new = not isinstance(context, models.Enrollment)
        if not is_new and context.study != field.data:
            raise wtforms.ValidationError(request.localizer.translate(_(
                u'Cannot change an enrollment\'s study.')))

    def check_consent_timeline(form, field):
        start = form.study.data.start_date
        end = form.study.data.end_date
        consent = form.consent_date.data
        latest = form.latest_consent_date.data
        if start is None:
            raise wtforms.ValidationError(request.localizer.translate(_(
                u'Study has not started yet.')))
        if consent < start:
            raise wtforms.ValidationError(request.localizer.translate(
                _('Cannot enroll before the study start date: ${date}'),
                mapping={'date': start.isoformat()}))
        if not (consent <= latest):
            raise wtforms.ValidationError(request.localizer.translate(
                _(u'Inconsistent enrollment dates')))
        if end and latest > end:
            raise wtforms.ValidationError(request.localizer.translate(
                _('Cannot enroll after the study end date: ${date}'),
                mapping={'date': end.isoformat()}))

    def check_termination_timeline(form, field):
        latest = form.latest_consent_date.data
        termination = form.termination_date.data
        end = form.study.data.end_date
        if form.study.data.termination_schema:
            return
        if latest is None or termination is None:
            return
        if termination < latest:
            raise wtforms.ValidationError(request.localizer.translate(
                _(u'Inconsistent termination dates')))
        if end and termination > end:
            raise wtforms.ValidationError(request.localizer.translate(
                _('Cannot terminate after the study end date: ${date}'),
                mapping={'date': end.isoformat()}))

    def check_reference(form, field):
        study = form.study.data
        number = form.reference_number.data
        if not study.check(number):
            raise wtforms.ValidationError(request.localizer.translate(
                _(u'Invalid reference number format for this study')))
        query = (
            Session.query(models.Enrollment)
            .filter_by(study=study, reference_number=number))
        if isinstance(context, models.Enrollment):
            query = query.filter(models.Enrollment.id != context.id)
        (exists,) = Session.query(query.exists()).one()
        if exists:
            raise wtforms.ValidationError(request.localizer.translate(
                _(u'Reference number already in use.')))

    def check_unique(form, field):
        if isinstance(context, models.EnrollmentFactory):
            patient = context.__parent__
        else:
            patient = context.patient
        query = (
            Session.query(models.Enrollment)
            .filter_by(
                patient=patient,
                study=form.study.data,
                consent_date=form.consent_date.data))
        if isinstance(context, models.Enrollment):
            query = query.filter(models.Enrollment.id != context.id)
        (exists,) = Session.query(query.exists()).one()
        if exists:
            raise wtforms.ValidationError(request.localizer.translate(_(
                u'This enrollment already exists.')))

    class EnrollmentForm(Form):
        study = ModelField(
            session=Session,
            class_=models.Study,
            validators=[
                wtforms.validators.InputRequired(),
                check_cannot_edit_study])
        consent_date = DateField(
            validators=[
                wtforms.validators.InputRequired(),
                check_unique])
        latest_consent_date = DateField(
            validators=[
                wtforms.validators.InputRequired(),
                check_consent_timeline])
        termination_date = DateField(
            validators=[
                wtforms.validators.Optional(),
                check_termination_timeline])
        reference_number = wtforms.StringField(
            validators=[
                wtforms.validators.Optional(),
                check_reference])

    return EnrollmentForm
