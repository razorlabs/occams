from datetime import datetime

from good import *  # NOQA
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.session import check_csrf_token
from pyramid.view import view_config
import six
from sqlalchemy import orm

from .. import _, models, Session
from ..validators import invalid2dict, Model


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
        '__url__': request.route_path('enrollment',
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
            'arm': None if not can_randomize or study.is_blinded else {
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

    schema = EnrollmentSchema(context, request)

    try:
        data = schema(request.json_body)
    except Invalid as e:
        raise HTTPBadRequest(json={'errors': invalid2dict(e)})

    if isinstance(context, models.EnrollmentFactory):
        enrollment = models.Enrollment(
            patient=context.__parent__, study=data['study'])
    else:
        enrollment = context

    enrollment.patient.modify_date = datetime.now()
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
    list(map(Session.delete, context.entities))
    context.patient.modify_date = datetime.now()
    Session.delete(context)
    Session.flush()
    request.session.flash(_(u'Deleted sucessfully'))
    return {'__next__': request.route_path('patient',
                                           patient=context.patient.pid)}


def EnrollmentSchema(context, request):

    def check_cannot_edit_study(value):
        if isinstance(context, models.Enrollment) and context.study != value:
            raise Invalid(request.localizer.translate(_(
                u'Cannot change an enrollment\'s study.')))
        return value

    def check_timeline(value):
        start = value['study'].start_date
        end = value['study'].end_date
        consent = value['consent_date']
        latest = value['latest_consent_date']
        if start is None:
            raise Invalid(request.localizer.translate(_(
                u'Study has not started yet.')))
        if consent < start:
            raise Invalid(request.localizer.translate(
                _('Cannot enroll before the study start date: ${date}'),
                mapping={'date': start.isoformat()}))
        if not (consent <= latest):
            raise Invalid(request.localizer.translate(
                _(u'Inconsistent enrollment dates')))
        if end and latest > end:
            raise Invalid(request.localizer.translate(
                _('Cannot enroll after the study end date: ${date}'),
                mapping={'date': end.isoformat()}))
        return value

    def check_reference(value):
        lz = request.localizer
        study = value['study']
        number = value['reference_number']
        if number is None:
            return value
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
            raise Invalid(lz.translate(_(u'Reference number already in use.')))
        return value

    def check_unique(value):
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
            raise Invalid(request.localizer.translate(_(
                u'This enrollment already exists.')))
        return value

    return Schema(All({
        'study': All(
            Model(models.Study, localizer=request.localizer),
            check_cannot_edit_study),
        'consent_date': Date('%Y-%m-%d'),
        'latest_consent_date': Date('%Y-%m-%d'),
        'reference_number': Maybe(Type(*six.string_types)),
        Extra: Remove
        },
        check_timeline,
        check_reference,
        check_unique))
