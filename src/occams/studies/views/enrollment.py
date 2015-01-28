from datetime import datetime

from pyramid.httpexceptions import HTTPBadRequest, HTTPOk
from pyramid.session import check_csrf_token
from pyramid.view import view_config
from sqlalchemy import orm
import wtforms
from wtforms.ext.dateutil.fields import DateField

from occams.forms.renderers import \
    make_form, render_form, apply_data, entity_data

from .. import _, models, Session
from ..utils import wtferrors, ModelField


@view_config(
    route_name='enrollments',
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
    route_name='enrollment',
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
            'enrollment',
            patient=patient.pid,
            enrollment=enrollment.id),
        '__randomize_url__': request.route_path(
            'enrollment_randomization',
            patient=patient.pid,
            enrollment=enrollment.id),
        '__termination_url__': request.route_path(
            'enrollment_termination',
            patient=patient.pid,
            enrollment=enrollment.id),
        '__can_edit__':
            bool(request.has_permission('edit', context)),
        '__can_terminate__':
            bool(request.has_permission('terminate', context)),
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
            'stop_date': (study.end_date and study.end_date.isoformat()),
            },
        'stratum': None if not study.is_randomized else {
            'id': enrollment.stratum.id,
            'arm': None if study.is_blinded or not can_randomize else {
                'id': enrollment.stratum.arm.id,
                'name': enrollment.stratum.arm.name,
                'title': enrollment.stratum.arm.title,
                },
            'randid': (
                enrollment.stratum.randid if not study.is_blinded else None)
            },
        'consent_date': enrollment.consent_date.isoformat(),
        'latest_consent_date': enrollment.latest_consent_date.isoformat(),
        'termination_date': (
            enrollment.termination_date
            and enrollment.termination_date.isoformat()),
        'reference_number': enrollment.reference_number,
        'stratum_id': enrollment.stratum.id if study.is_randomized else None
        }


@view_config(
    route_name='enrollments',
    permission='add',
    xhr=True,
    request_method='POST',
    renderer='json')
@view_config(
    route_name='enrollment',
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
    enrollment.reference_number = form.reference_number.data

    Session.flush()
    return view_json(enrollment, request)


@view_config(
    route_name='enrollment',
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
    return {'__next__': request.route_path('patient',
                                           patient=context.patient.pid)}


@view_config(
    route_name='enrollment_termination',
    permission='terminate',
    xhr=True,
    renderer='string')
def terminate_ajax(context, request):
    try:
        entity = (
            Session.query(models.Entity)
            .join(models.Context)
            .filter_by(external='enrollment', key=context.id)
            .one())
    except orm.exc.MultipleResultsFound:
        raise Exception('Should only have one...')
    except orm.exc.NoResultFound:
        entity = None
        schema = context.study.termination_schema
        data = {}
    else:
        schema = entity.schema
        data = entity_data(entity)
    Form = make_form(Session, schema)
    form = Form(request.POST, data=data)

    if request.method == 'POST':
        check_csrf_token(request)
        if form.validate():
            if not entity:
                # changing termination version *should* not be
                # allowed, just assign the schema that's already being used
                entity = models.Entity(schema=schema)
                context.entities.add(entity)
            upload_dir = request.registry.settings['app.blob.dir']
            apply_data(Session, entity, form.data, upload_dir)
            context.termination_date = form.termination_date.data
            Session.flush()
            return HTTPOk(json=view_json(context, request))
        else:
            return HTTPBadRequest(json={'errors': wtferrors(form)})

    return render_form(form, attr={
        'id': 'enrollment-termination',
        'method': 'POST',
        'action': request.current_route_path(),
        'role': 'form',
        'data-bind': 'formentry: {}, submit: $root.terminateEnrollment'
    })


def EnrollmentSchema(context, request):

    def check_cannot_edit_study(form, field):
        is_new = not isinstance(context, models.Enrollment)
        if not is_new and context.study != field.data:
            raise wtforms.ValidationError(request.localizer.translate(_(
                u'Cannot change an enrollment\'s study.')))

    def check_timeline(form, field):
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

    class EnrollmentForm(wtforms.Form):
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
                check_timeline])
        reference_number = wtforms.StringField(
            validators=[
                wtforms.validators.Optional(),
                check_reference])

    return EnrollmentForm
