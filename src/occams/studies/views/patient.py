from datetime import datetime
from pyramid.httpexceptions import HTTPBadRequest, HTTPNotFound
from pyramid.i18n import get_localizer
from pyramid.session import check_csrf_token
from pyramid.view import view_config
from sqlalchemy import orm
from voluptuous import *  # NOQA

from .. import _, models, Session
from ..widgets.pager import Pager


@view_config(
    route_name='patients',
    permission='patient_view',
    request_method='q',
    renderer='../templates/patient/search.pt')
def search(request):
    search_term = request.GET.get('q')

    if not search_term:
        return {}

    current_page = int(request.GET.get('page', 0))
    search_query = query_by_ids(search_term)
    search_count = search_query.count()
    pager = Pager(current_page, 10, search_count)
    return {'pager': pager}


@view_config(
    route_name='patient',
    permission='patient_view',
    request_method='GET',
    renderer='../templates/patient/view.pt')
def view(request):
    reference_types_query = (
        Session.query(models.ReferenceType)
        .order_by(models.ReferenceType.title.asc()))
    patient = get_patient(request)
    return {
        'available_sites': [{
            'id': s.id,
            'name': s.name,
            'title': s.title
            } for s in get_available_sites(request)],
        'available_reference_types': [{
            'id': t.id,
            'name': t.name,
            'title': t.title
            } for t in reference_types_query],
        'patient': get_patient_data(request, patient),
        'enrollments': get_enrollments_data(request, patient),
        'visits': get_visits_data(request, patient)
    }


@view_config(
    route_name='patient',
    permission='patient_view',
    request_param='alt=json',
    request_method='GET',
    renderer='json')
@view_config(
    route_name='patient',
    permission='patient_view',
    request_method='GET',
    xhr=True,
    renderer='json')
def view_json(request):
    return get_patient_data(request, get_patient(request))


@view_config(
    route_name='patient',
    permission='patient_edit',
    xhr=True,
    request_method='PUT',
    renderer='json')
def edit_json(request):
    check_csrf_token(request)
    patient = get_patient(request)
    schema = PatientSchema(request, patient)
    try:
        data = schema(request.json_body)
    except MultipleInvalid as exc:
        raise HTTPBadRequest(json={
            'validation_errors': dict(
                [('-'.join(map(str, e.path)), e.msg) for e in exc.errors])})
    apply_changes(patient, data)
    return get_patient_data(request, patient)


def apply_changes(patient, data):
    patient.site_id = data['site_id']
    if data['references']:
        incoming = set([(r['reference_type_id'], r['reference_number'])
                        for r in data['references']])
        # make a copy of the list so we can remove from the original
        current = [r for r in patient.references]
        for r in current:
            key = (r.reference_type_id, r.reference_number)
            if key not in incoming:
                patient.references.remove(r)
            else:
                incoming.remove(key)

        for reference_type_id, reference_number in incoming:
            patient.references.append(models.PatientReference(
                reference_type_id=reference_type_id,
                reference_number=reference_number))

    Session.flush()
    return patient


def get_patient_data(request, patient):
    p = patient
    return {
        '__src__': request.route_path('patient', patient=p.pid),
        'id': p.id,
        'site_id': p.site_id,
        'pid': p.pid,
        'references': [{
            'id': r.id,
            'reference_type_id': r.reference_type.id,
            'reference_number': r.reference_number,
            } for r in p.references],
        'modify_date': p.modify_date.isoformat(),
        'modify_user': p.modify_user.key,
        'create_date': p.create_date.isoformat(),
        'create_user': p.create_user.key
        }


def get_enrollments_data(request, patient):
    return [{
        '__src__': request.route_path('enrollment',
                                      enrollment=e.id),
        'study': {
            'name': e.study.name,
            'title': e.study.title,
            'is_blinded': e.study.is_blinded
            },
        'consent_date': e.consent_date.isoformat(),
        'latest_consent_date': e.latest_consent_date.isoformat(),
        'termination_date': (
            e.termination_date and e.termination_date.isoformat()),
        'reference_number': e.reference_number,
        'stratum': e.stratum and {
            'randid': e.stratum.randid,
            'arm': None if e.study.is_blinded else {
                'name': e.stratum.arm.name,
                'title': e.stratum.arm.title,
                }
            }
        } for e in patient.enrollments],


def get_visits_data(request, patient):
    return [{
        '__src__': request.route_path('visit',
                                      patient=patient.pid,
                                      visit=v.visit_date.isoformat()),
        'cycles': [{
            'study': {
                'name': c.study.name,
                'title': c.study.title,
                'code': c.study.code
                },
            'name': c.name,
            'title': c.title,
            'week': c.week
            } for c in v.cycles],
        'visit_date': v.visit_date.isoformat(),
        'num_complete': len([e for e in v.entities
                             if e.state.name == 'complete']),
        'total_forms': len(v.entities),
        } for v in patient.visits],


def get_patient(request):
    """
    Uses the URL dispatch matching dictionary to find a study
    """
    try:
        patient = (
            Session.query(models.Patient)
            .filter_by(pid=request.matchdict['patient']).one())
        request.session.setdefault('viewed', {})
        request.session['viewed'][patient.pid] = {
            'pid': patient.pid,
            'view_date': datetime.now()
        }
        request.session.changed()
        return patient
    except orm.exc.NoResultFound:
        raise HTTPNotFound


def get_available_sites(request):
    # TODO: Only include the sites the user is a member of
    sites_query = Session.query(models.Site).order_by(models.Site.title)
    return sites_query


def query_by_ids(term):
    """
    Search utility that returns a patient entry query based on
    reference numbers
    """
    wildcard = '%{0}%'.format(term)
    return (
        Session.query(models.Patient)
        .outerjoin(models.Patient.enrollments)
        .outerjoin(models.Patient.strata)
        .outerjoin(models.Patient.reference_numbers)
        .filter(
            models.Patient.pid.ilike(wildcard)
            | models.Enrollment.reference_number.ilike(wildcard)
            | models.Stratum.reference_number.ilike(wildcard)
            | models.PatientReference.reference_number.ilike(wildcard)
            | models.Patient.initials.ilike(wildcard))
        .order_by(models.Patient.pid.asc()))


def validate_unique_reference(request, patient):
    def validator(value):
        reference_query = (
            Session.query(models.PatientReference)
            .filter_by(
                id=value['reference_type_id'],
                reference_number=value['reference_number'])
            .filter(models.PatientReference.patient != patient))
        reference = reference_query.first()
        if reference:
            # Need to translate before sending back to client
            ts = _(u'${type} ${number} is already assigned to ${pid}',
                   mapping={'type': reference.reference_type.title,
                            'number': reference.reference_number,
                            'pid': reference.patient.pid})
            msg = get_localizer(request).translate(ts)
            raise Invalid(msg, path=['reference_number'])
        return value
    return validator


def PatientSchema(request, patient):
    valid_sites = [s.id for s in get_available_sites(request)]
    valid_types = [r.id for r in Session.query(models.ReferenceType)]
    lz = get_localizer(request)
    return Schema({
        Required('site_id'): All(
            Coerce(int),
            Any(*valid_sites,
                msg=lz.translate(_('Invalid site')))),
        Optional('references'): [All({
            Required('reference_type_id'): All(
                Coerce(int),
                Any(*valid_types,
                    msg=lz.translate(_(u'Invalid type')))),
            Required('reference_number'): Coerce(str),
            Extra: object
        }, validate_unique_reference(request, patient))],
        Extra: object
    })
