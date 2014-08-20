from datetime import datetime
from pyramid.httpexceptions import HTTPBadRequest, HTTPNotFound
from pyramid.i18n import get_localizer
from pyramid.session import check_csrf_token
from pyramid.view import view_config
import six
from sqlalchemy import orm
from voluptuous import *  # NOQA

from .. import _, models, Session

@view_config(
    route_name='patient_enrollments',
    permission='enrollment_add',
    xhr=True,
    request_method='POST',
    renderer='json')
def enrollments_edit_json(request):
    check_csrf_token(request)
    patient = get_patient(request)
    schema = EnrollmentSchema(request, patient)
    try:
        data = schema(request.json_body)
    except MultipleInvalid as exc:
        raise HTTPBadRequest(json={
            'validation_errors': [e.error_message for e in exc.errors]})
    return get_patient_data(request, patient)

def get_enrollments_data(request, patient):
    return [{
        '__url__': request.route_path('enrollment', enrollment=e.id),
        'id': e.id,
        'study': {
            'id': e.study.id,
            'name': e.study.name,
            'title': e.study.title,
            'is_randomized': e.study.is_randomized,
            'is_blinded': e.study.is_blinded
            },
        'stratum': None if not e.study.is_randomized else {
            'id': e.stratum.id,
            'arm': None if e.study.is_blinded else {
                'id': e.stratum.arm.id,
                'name': e.stratum.arm.name,
                'title': e.stratum.arm.title,
                },
            'randid': e.stratum.randid
            },
        'consent_date': e.consent_date.isoformat(),
        'latest_consent_date': e.latest_consent_date.isoformat(),
        'termination_date': (
            e.termination_date and e.termination_date.isoformat()),
        'reference_number': e.reference_number,
        'stratum_id': None if not e.study.is_randomized else e.stratum.id
        } for e in patient.enrollments]

