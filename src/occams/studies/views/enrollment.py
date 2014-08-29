from pyramid.httpexceptions import HTTPBadRequest
from pyramid.i18n import get_localizer
from pyramid.session import check_csrf_token
from pyramid.view import view_config

from sqlalchemy import orm
from voluptuous import *  # NOQA

from .. import models, Session
from ..validators import Date


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

    schema = EnrollmentSchema(context, request)

    try:
        data = schema(request.json_body)
    except MultipleInvalid as exc:
        raise HTTPBadRequest(json={
            'validation_errors': [e.error_message for e in exc.errors]})

    if isinstance(context, models.EnrollmentFactory):
        patient = context.__parent__
        enrollment = models.Enrollment(patient=patient, study=data['study'])

    enrollment.consent_date = data['consent_date']
    enrollment.latest_consent_date = data['latest_consent_date']
    enrollment.reference_number = data['reference_number']

    Session.flush()
    return view_json(enrollment, request)


@view_config(
    route_name='enrollment',
    permission='delete',
    request_method='DELETE',
    xhr=True,
    renderer='json')
def delete_json(context, request):
    Session.delete(context)
    Session.flush()
    request.session.flash(_(u'Deleted sucessfully'))
    return {'__next__': request.current_route_path(_route_name='patient')}


def EnrollmentSchema(context, request):
    return Schema(All({
        Required('study'): All(Coerce(int), coerce_study(context, request)),
        Required('consent_date'): Date(),
        Required('latest_consent_date'): Date(),
        Optional('reference_number'): Coerce(str),
        Extra: object
        },
        check_timeline(context, request),
        check_reference(context, request),
        check_unique(context, request)))


def coerce_study(context, request):
    """
    Returns a validator that extracts a study object
    """
    def validator(value):
        lz = get_localizer(request)
        study = Session.query(models.Study).get(value)
        if study is None:
            raise Invalid(lz.translate(_(
                u'Study does not exist')))
        return study
    return validator


def check_timeline(context, request):
    """
    Returns a validator that checks the enrollment timeline
    """
    def validator(value):
        lz = get_localizer(request)
        start = value['study'].start_date
        stop = value['study'].stop_date
        consent = value['consent_date']
        latest = value['latest_consent_date']
        if consent < start:
            raise Invalid(la.translate(
                _('Cannot enroll before the study start date: ${date}'),
                mapping={'date': start.isoformat()}))
        if not (consent <= latest):
            raise Invalid(lz.translate(_(u'Inconsistent enrollment dates')))
        if stop and latest < stop:
            raise Invalid(lz.translate(
                _('Cannot enroll after the study stop date: ${date}'),
                mapping={'date': stop.isoformat()}))
        return value
    return validator


def check_reference(context, request):
    """
    Returns a validator that checks the reference number is valid for the study
    """
    def validator(value):
        lz = get_localizer(request)
        study = value['study']
        number = value['reference_number']
        if not study.check_reference_number(number):
            raise Invalid(
                _(u'Invalid reference number format for this study'))
        query = (
            Session.query(models.Enrollment)
            .filter_by(study=study, reference_number=number))
        if isinstance(context, models.Enrollment):
            query = query.filter(models.Enrollment.id != context.id)
        (exists,) = Session.query(query.exists()).one()
        if exists:
            raise Invalid(lz.translate(_(u'Reference number is already used')))
        return value
    return validator


def check_unique(context, request):
    """
    Ensures the patient is not already enrolled (via consent date)
    """
    def validator(value):
        lz = get_localizer(request)
        if isinstance(context, models.EnrollmentFactory):
            patient = context.__parent__
        else:
            patient = context.patient
        query = (
            Session.query(models.Enrollment)
            .filter_by(
                patient=patient,
                study=value['study'],
                consent_date=value['consent_date']))
        if isinstance(context, models.Enrollment):
            query = query.filter(models.Enrollment.id != context.id)
        (exists,) = Session.query(query.exists()).one()
        if exists:
            raise Invalid(lz.translate(_(
                u'This enrollment already exists')))
        return value
    return validator
