from datetime import datetime, date
import uuid

from pyramid.httpexceptions import \
    HTTPBadRequest, HTTPFound, HTTPOk, HTTPNotFound
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
from occams_datastore import models as datastore
from occams_datastore.reporting import build_report

from .. import _, log, models


RAND_CHALLENGE, RAND_ENTER, RAND_VERIFY = range(3)

RAND_INFO_KEY = 'randomization_info'


@view_config(
    route_name='studies.enrollments',
    permission='view',
    xhr=True,
    renderer='json')
def list_json(context, request):
    db_session = request.db_session
    patient = context.__parent__
    enrollments_query = (
        db_session.query(models.Enrollment)
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
        '__can_terminate__': bool(
            request.has_permission('terminate', context) and
            study.termination_schema),
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
            enrollment.termination_date and
            enrollment.termination_date.isoformat()),
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
    db_session = request.db_session

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
    enrollment.reference_number = form.reference_number.data

    if not form.study.data.termination_schema:
        enrollment.termination_date = form.termination_date.data

    db_session.flush()
    return view_json(enrollment, request)


@view_config(
    route_name='studies.enrollment',
    permission='delete',
    request_method='DELETE',
    xhr=True,
    renderer='json')
def delete_json(context, request):
    db_session = request.db_session
    list(map(db_session.delete, context.entities))
    context.patient.modify_date = datetime.now()
    db_session.delete(context)
    db_session.flush()
    request.session.flash(_(u'Deleted sucessfully'))
    return {'__next__': request.route_path('studies.patient',
                                           patient=context.patient.pid)}


@view_config(
    route_name='studies.enrollment_termination',
    permission='terminate',
    xhr=True,
    renderer='string')
def terminate_ajax(context, request):
    db_session = request.db_session
    try:
        entity = (
            db_session.query(datastore.Entity)
            .join(datastore.Entity.schema)
            .filter(datastore.Schema.name.in_(
                # Only search for forms being used as temrination forms
                db_session.query(datastore.Schema.name)
                .join(models.Study.termination_schema)
                .subquery()))
            .join(datastore.Context)
            .filter_by(external='enrollment', key=context.id)
            .one())
    except orm.exc.MultipleResultsFound:
        raise Exception('Should only have one...')
    except orm.exc.NoResultFound:
        schema = context.study.termination_schema
        entity = datastore.Entity(schema=schema)
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
            db_session.query(datastore.State)
            .filter_by(name='pending-entry')
            .one())

    if 'termination_date' not in schema.attributes:
        msg = 'There is no "termination_date" configured on: {}'
        log.warn(msg.format(schema.name))

    if request.has_permission('retract'):
        transition = modes.ALL
    elif request.has_permission('transition'):
        transition = modes.AVAILABLE
    else:
        transition = modes.AUTO

    Form = make_form(
        db_session, schema,
        entity=entity, transition=transition, show_metadata=False)

    form = Form(request.POST, data=entity_data(entity))

    def validate_termination_date(form, field):
        if not (field.data >= context.latest_consent_date):
            raise wtforms.ValidationError(request.localizer.translate(
                _(u'Termination must be on or after latest consent (${date})'),
                mapping={'date': context.latest_consent_date}
            ))

    # Inject a validator into the termination form so that we
    # ensure that the termination date provided is valid
    form.termination_date.validators.append(validate_termination_date)

    if request.method == 'POST':
        check_csrf_token(request)
        if form.validate():
            if not entity.id:
                # changing termination version *should* not be
                # allowed, just assign the schema that's already being used
                context.entities.add(entity)
            upload_dir = request.registry.settings['studies.blob.dir']
            apply_data(db_session, entity, form.data, upload_dir)
            context.termination_date = form.termination_date.data
            db_session.flush()
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


def _get_randomized_form(context, request):
    db_session = request.db_session
    try:
        entity = (
            db_session.query(datastore.Entity)
            .join(datastore.Entity.contexts)
            .filter_by(external='stratum', key=context.stratum.id)
            .one())
    except orm.exc.MultipleResultsFound:
        raise Exception('Should only have one...')
    except orm.exc.NoResultFound:
        raise HTTPNotFound()
    else:
        Form = make_form(db_session, entity.schema, show_metadata=False)
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
    form = _get_randomized_form(context, request)
    return {'form': render_form(form, disabled=True)}


@view_config(
    route_name='studies.enrollment_randomization',
    permission='randomize',
    xhr=True,
    renderer='json')
def randomize_ajax(context, request):
    """
    Procesess a patient's randomiation by conmpleting randomization form

    Rules:

    * The user can only randomize one patient at a time.
    * If another randomization is in progress, both are restarted.
    * A randomization session may not "continue" from another.

    In order to address a single randomization at a time, the process assigns
    a "process id" or ``procid`` for the duration of the process, this way
    if a new process begins it will have a different token which will not
    match the current process and nullify everything. This is done by
    passing the ``procid`` via POST or GET depending on the phase of data
    entry and matching it against the session-stored ``procid``. If the they
    do not match, the operation is cancelled.

    The process goes as follows:

    # CHALLENGE: Upon first request the user will be issued a ``procid``
      token this token will remain unchainged for the duration of the
      randomization process. If it changes, the process restarts. The goal
      of the challenge stage is to ensure the user confirms their intent
      to randomize.
    # ENTER: After passing the challenge stage, the user will then have
      oppertunity to enter the randomization schema form data that will
      be used to determine assignement to the study arm.
    # VERIFY: The user will then have to verify the data again to ensure
      accurate responses. If the user fails this stage, they will have
      to pass the ENTER stage again. Upon sucessfull verification the
      ``procid`` expires and the patient is randomized. The user will not
      be shown the challenge/entry forms again and only the randomization
      information information will be rendered for future reference to the
      user.
    """

    db_session = request.db_session
    enrollment = context

    if not enrollment.is_randomized:
        # Ensure a ``procid`` is assigned for the duration of the process
        # This way, if a new request mismatches, we can expire the operation
        if 'procid' not in request.GET and 'procid' not in request.POST:
            internal_procid = str(uuid.uuid4())
            request.session[RAND_INFO_KEY] = {
                'procid': internal_procid,
                'stage': RAND_CHALLENGE,
                'formdata': None
            }
            return HTTPFound(
               location=request.current_route_path(
                    _query={'procid': internal_procid}))

        external_procid = request.GET.get('procid') or request.POST.get('procid')
        internal_procid = request.session.get(RAND_INFO_KEY, {}).get('procid')

        if external_procid is not None and external_procid != internal_procid:
            try:
                del request.session[RAND_INFO_KEY]
            except KeyError:
                pass
            request.session.flash(
                _(u'You have another randomization in progress, '
                  u'starting over.'),
                'warning')
            return HTTPFound(location=request.current_route_path(_query={}))

    if request.method == 'POST':
        check_csrf_token(request)

        if enrollment.is_randomized:
            request.session.flash(
                _(u'This patient is already randomized for this study'),
                'warning')
            return HTTPFound(location=request.current_route_path(_query={}))

        if request.session[RAND_INFO_KEY]['stage'] == RAND_CHALLENGE:
            Form = _make_challenge_form(enrollment, request)
            form = Form(request.POST)
            if not form.validate():
                raise HTTPBadRequest(json={'errors': wtferrors(form)})
            else:
                request.session[RAND_INFO_KEY]['stage'] = RAND_ENTER
                request.session.changed()
                return HTTPFound(location=request.current_route_path(
                    _query={'procid': internal_procid}))

        elif request.session[RAND_INFO_KEY]['stage'] == RAND_ENTER:
            Form = make_form(
                db_session,
                enrollment.study.randomization_schema,
                show_metadata=False)
            form = Form(request.POST)
            if not form.validate():
                raise HTTPBadRequest(json={'errors': wtferrors(form)})
            else:
                request.session[RAND_INFO_KEY]['stage'] = RAND_VERIFY
                request.session[RAND_INFO_KEY]['formdata'] = form.data
                request.session.changed()
                return HTTPFound(location=request.current_route_path(
                    _query={'procid': internal_procid}))

        elif request.session[RAND_INFO_KEY]['stage'] == RAND_VERIFY:
            Form = make_form(
                db_session,
                enrollment.study.randomization_schema,
                show_metadata=False)
            form = Form(request.POST)
            if not form.validate():
                raise HTTPBadRequest(json={'errors': wtferrors(form)})
            else:
                previous_data = \
                    request.session[RAND_INFO_KEY].get('formdata') or {}
                # ensure entered values match previous values
                for field, value in form.data.items():
                    if value != previous_data.get(field):
                        # start over
                        request.session[RAND_INFO_KEY]['stage'] = RAND_ENTER
                        request.session[RAND_INFO_KEY]['formdata'] = None
                        request.session.flash(
                            _(u'Your responses do not match previously '
                              u'entered responses. '
                              u'You will need to reenter your responses.'),
                            'warning')
                        break
                else:
                    report = build_report(
                        db_session, enrollment.study.randomization_schema.name)
                    data = form.data

                    # Get an unassigned entity that matches the input criteria
                    query = (
                        db_session.query(models.Stratum)
                        .filter(models.Stratum.study == enrollment.study)
                        .filter(models.Stratum.patient == sa.null())
                        .join(models.Stratum.contexts)
                        .join(datastore.Context.entity)
                        .add_entity(datastore.Entity)
                        .join(report, report.c.id == datastore.Entity.id)
                        .filter(sa.and_(
                            *[(getattr(report.c, k) == v)
                                for k, v in data.items()]))
                        .order_by(models.Stratum.id.asc())
                        .limit(1))

                    try:
                        (stratum, entity) = query.one()
                    except orm.exc.NoResultFound:
                        raise HTTPBadRequest(
                            body=_(u'Randomization numbers depleted'))

                    # so far so good, set the contexts and complete the request
                    stratum.patient = enrollment.patient
                    entity.state = (
                        db_session.query(datastore.State)
                        .filter_by(name=u'complete')
                        .one())
                    entity.collect_date = date.today()
                    enrollment.patient.entities.add(entity)
                    enrollment.entities.add(entity)
                    db_session.flush()
                    del request.session[RAND_INFO_KEY]
                    request.session.flash(
                        _(u'Randomization complete'), 'success')
                    return HTTPFound(
                        location=request.current_route_path(_query={}))

        else:
            request.session.flash(
                _(u'Unable to determine randomization state. Restarting'),
                'warning')
            del request.session[RAND_INFO_KEY]
            return HTTPFound(location=request.current_route_path(_query={}))

    if enrollment.is_randomized:
        template = '../templates/enrollment/randomize-view.pt'
        form = _get_randomized_form(enrollment, request)
    elif request.session[RAND_INFO_KEY]['stage'] == RAND_CHALLENGE:
        template = '../templates/enrollment/randomize-challenge.pt'
        Form = _make_challenge_form(enrollment, request)
        Form.procid = wtforms.HiddenField()
        form = Form(procid=internal_procid)
        form.meta.entity = None
        form.meta.schema = enrollment.study.randomization_schema
    elif request.session[RAND_INFO_KEY]['stage'] == RAND_ENTER:
        template = '../templates/enrollment/randomize-enter.pt'
        Form = make_form(
            db_session,
            enrollment.study.randomization_schema,
            show_metadata=False)
        Form.procid = wtforms.HiddenField()
        form = Form(procid=internal_procid)
    elif request.session[RAND_INFO_KEY]['stage'] == RAND_VERIFY:
        template = '../templates/enrollment/randomize-verify.pt'
        Form = make_form(
            db_session,
            enrollment.study.randomization_schema,
            show_metadata=False)
        form = Form()
        Form.procid = wtforms.HiddenField()
        form = Form(procid=internal_procid)

    return {
        'is_randomized': enrollment.is_randomized,
        'enrollment': view_json(enrollment, request),
        'content': render(template, {
            'context': enrollment,
            'request': request,
            'form': render_form(
                form,
                disabled=enrollment.is_randomized,
                show_footer=False,
                attr={
                    'id': 'enrollment-randomization',
                    'method': 'POST',
                    'action': request.current_route_path(),
                    'role': 'form',
                    'data-bind':
                        'formentry: {}, submit: $root.randomizeEnrollment'
                })
        })
    }


def EnrollmentSchema(context, request):
    db_session = request.db_session

    def check_cannot_edit_study(form, field):
        is_new = not isinstance(context, models.Enrollment)
        if not is_new and context.study != field.data:
            raise wtforms.ValidationError(request.localizer.translate(_(
                u'Cannot change an enrollment\'s study.')))

    def check_consent_timeline(form, field):
        consent = form.consent_date.data
        latest = form.latest_consent_date.data
        # This validator is used on both latest_consent and consent,
        # so we need to check that both have been validated before proceeding.
        if consent and latest and not consent <= latest:
            raise wtforms.ValidationError(request.localizer.translate(
                _(u'Inconsistent consent dates')))

    def check_termination_timeline(form, field):
        latest = form.latest_consent_date.data
        termination = form.termination_date.data
        if form.study.data.termination_schema:
            return
        if latest is None or termination is None:
            return
        if termination < latest:
            raise wtforms.ValidationError(request.localizer.translate(
                _(u'Inconsistent termination dates')))

    def check_reference(form, field):
        study = form.study.data
        number = form.reference_number.data
        if not study.check(number):
            raise wtforms.ValidationError(request.localizer.translate(
                _(u'Invalid reference number format for this study')))
        query = (
            db_session.query(models.Enrollment)
            .filter_by(study=study, reference_number=number))
        if isinstance(context, models.Enrollment):
            query = query.filter(models.Enrollment.id != context.id)
        (exists,) = db_session.query(query.exists()).one()
        if exists:
            raise wtforms.ValidationError(request.localizer.translate(
                _(u'Reference number already in use.')))

    def check_unique(form, field):
        if isinstance(context, models.EnrollmentFactory):
            patient = context.__parent__
        else:
            patient = context.patient
        query = (
            db_session.query(models.Enrollment)
            .filter_by(
                patient=patient,
                study=form.study.data,
                consent_date=form.consent_date.data))
        if isinstance(context, models.Enrollment):
            query = query.filter(models.Enrollment.id != context.id)
        (exists,) = db_session.query(query.exists()).one()
        if exists:
            raise wtforms.ValidationError(request.localizer.translate(_(
                u'This enrollment already exists.')))

    class EnrollmentForm(Form):
        study = ModelField(
            db_session=db_session,
            class_=models.Study,
            validators=[
                wtforms.validators.InputRequired(),
                check_cannot_edit_study])
        consent_date = DateField(
            validators=[
                wtforms.validators.InputRequired(),
                check_unique,
                check_consent_timeline])
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
