from pyramid.httpexceptions import HTTPBadRequest
from pyramid.session import check_csrf_token
from pyramid.view import view_config

from sqlalchemy import orm
from voluptuous import *  # NOQA

from .. import models, Session


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
def manage_json(context, request):
    check_csrf_token(request)

    if request.method == 'PUT':
        enrollment = context
        patient = enrollment.patient
    else:
        enrollment = None
        patient = contet.__parent__

    schema = EnrollmentSchema(request, patient)

    try:
        data = schema(request.json_body)
    except MultipleInvalid as exc:
        raise HTTPBadRequest(json={
            'validation_errors': [e.error_message for e in exc.errors]})

    if request.method == 'POST':
        study = (
            Session.query(models.Study)
            .filter_by(id=data['study_id'])
            .one())
        enrollment = models.Enrollment(patient=patient, study=study)

    enrollment.consent_date = data['consent_date']
    enrollment.latest_consent_date = data['latest_consent_date']
    enrollment.termination_date = data['termination_date']
    enrollment.reference_number = data['reference_number']

    Session.flush()
    return view_json(enrollment, request)


@view_config(
    route_name='enrollment',
    permission='view',
    xhr=True,
    renderer='json')
def view_json(context, request):
    enrollment = context
    patient = context.patient
    return {
        '__url__': request.route_path('enrollment',
                                      patient=patient.pid,
                                      enrollment=enrollment.id),
        'id': enrollment.id,
        'study': {
            'id': enrollment.study.id,
            'name': enrollment.study.name,
            'title': enrollment.study.title,
            'is_randomized': enrollment.study.is_randomized,
            'is_blinded': enrollment.study.is_blinded,
            'start_date': enrollment.study.start_date.isoformat(),
            'stop_date': (
                enrollment.study.stop_date
                and enrollment.study.stop_date.isoformat()),
            },
        'stratum': None if not enrollment.study.is_randomized else {
            'id': enrollment.stratum.id,
            'arm': None if enrollment.study.is_blinded else {
                'id': enrollment.stratum.arm.id,
                'name': enrollment.stratum.arm.name,
                'title': enrollment.stratum.arm.title,
                },
            'randid': enrollment.stratum.randid
            },
        'consent_date': enrollment.consent_date.isoformat(),
        'latest_consent_date': enrollment.latest_consent_date.isoformat(),
        'termination_date': (
            enrollment.termination_date
            and enrollment.termination_date.isoformat()),
        'reference_number': enrollment.reference_number,
        'stratum_id': (
            None if not enrollment.study.is_randomized
            else enrollment.stratum.id)
        }
