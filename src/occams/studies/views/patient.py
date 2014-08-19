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
    patient = get_patient(request)
    return {
        'available_sites': get_available_sites(request),
        'available_reference_types': (
            Session.query(models.ReferenceType)
            .order_by(models.ReferenceType.title.asc())),
        'available_studies': (
            Session.query(models.Study)
            .order_by(models.Study.title.asc())),
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
            'validation_errors': dict(
                [('-'.join(map(str, e.path)), e.msg) for e in exc.errors])})
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
    return {
        '__url__': request.route_path('patient', patient=patient.pid),
        'id': patient.id,
        'site': {
            'id': patient.site.id,
            'name': patient.site.name,
            'title': patient.site.title
            },
        'pid': patient.pid,
        'references': [{
            '__meta__': {
                },
            'id': r.id,
            'reference_type': {
                'id': r.reference_type.id,
                'name': r.reference_type.name,
                'title': r.reference_type.title,
                },
            'reference_number': r.reference_number,
            } for r in patient.references],
        }


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


def get_visits_data(request, patient):
    return [{
        '__url__': request.route_path(
            'visit',
            patient=patient.pid,
            visit=v.visit_date.isoformat()),
        'id': v.id,
        'cycles': [{
            'id': c.id,
            'study': {
                'id': c.study.id,
                'name': c.study.name,
                'title': c.study.title,
                'code': c.study.code
                },
            'name': c.name,
            'title': c.title,
            'week': c.week
            } for c in v.cycles],
        'visit_date': v.visit_date.isoformat(),
        'forms_complete': len(
            [e for e in v.entities if e.state.name == 'complete']),
        'forms_total': len(v.entities)
        } for v in patient.visits]


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
        lz = get_localizer(request)
        reference_query = (
            Session.query(models.PatientReference)
            .filter_by(
                id=value['reference_type_id'],
                reference_number=value['reference_number'])
            .filter(models.PatientReference.patient != patient))
        reference = reference_query.first()
        if reference:
            # Need to translate before sending back to client
            msg = lz.translate(_(
                u'${type} ${number} is already assigned to ${pid}',
                mapping={
                    'type': reference.reference_type.title,
                    'number': reference.reference_number,
                    'pid': reference.patient.pid}))
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
            Any(*valid_sites, msg=lz.translate(_(u'Invalid site')))
            ),
        Optional('references'): [All({
            Required('reference_type_id'): All(
                Coerce(int),
                Any(*valid_types, msg=lz.translate(_(u'Invalid type')))
            ),
            Required('reference_number'): Coerce(str),
            Extra: object
            }, validate_unique_reference(request, patient))],
        Extra: object
        })


def Date(fmt='%Y-%m-%d', msg=None):
    def validator(value):
        try:
            datetime.strptime(v, fmt)
        except ValueError:
            raise Invalid(msg or u'Invalid date format, must be YYYY-MM-DD')
    return validator


def validate_study(request):
    def validator(value):
        lz = get_localizer(request)
        (exists,) = (
            Session.query(
                Session.query(models.Study)
                .filter_by(id=value)
                .exists()
            ).one())
        if not exists:
            raise Invalid(lz.translate(_(
                u'Specified a study that does not exist')))
        return value
    return validator


def validate_patient_enrollement(request, patient, enrollment=None):
    def validator(value):
        lz = get_localizer(request)
        if value['latest_consent_date'] < value['consent_date']:
            raise Invalid(lz.translate(_(
                u'Inconsitent consent dates')))
        if (value['termination_date']
                and value['termantion_date'] < value['latest_consent_date']):
            raise Invalid(lz.translate(_(
                u'Inconsitent termination date')))
        taken_query = (
            Session.query(models.Enrollment)
            .filter(models.Enrollment.patient == patient)
            .filter(models.Enrollment.study.has(id=value['study_id']))
            .filter(models.Enrollment.consent_date == value['consent_date']))
        if enrollment is not None:
            taken_query = \
                taken_query.filter(models.Enrollment.id != enrollmetn.id)
        taken = taken_query.first()
        if taken:
            raise Invalid(lz.translate(_(
                u'Enrollment for ${study_title} on ${consent_date} '
                u'is already used by ${pid}',
                mapping={
                    'study_title': taken.study.title,
                    'consent_date': taken.consent_date.isoformat(),
                    'pid': taken.patient.pid})))
        return value
    return validator


def EnrollmentSchema(request, patient, enrollment=None):
    return Schema(All({
        Required('study_id'): All(
            Coerce(int), validiate_study(request)),
        Required('consent_date'): Date(),
        Required('latest_consent_date'): Date(),
        Optional('termination_date'): Date(),
        Optional('reference_number'): str,
        Extra: object
        }, validate_patient_enrollment(request, patient, enrollment)))


def validate_visit_cycle(request, patient, visit=None):
    def validator(value):
        lz = get_localizer(request)
        (exists,) = (
            Session.query(
                Session.query(models.Cycle)
                .filter_by(id=value)
                .exists()
            ).one())
        if not exists:
            raise Invalid(lz.translate(_(
                u'Specified a cycle that does not exist')))
        # TODO need a mechanism to check if the cycle can be repeated,
        # for not just block all repetions, vaya con Dios...
        taken_query = (
            Session.query(model.Visit)
            .filter(model.Visit.patient == patient)
            .filter(models.Visit.cycles.any(id=value)))
        if visit:
            taken_query = taken_query.filter(model.Visit.id != visit.id)
        taken = taken_query.first()
        if taken:
            raise Invalid(lz.translate(_(
                u'Cycle is already being used by visit on ${visit_date}',
                mapping={'visit_date': taken.visit_date})))
        return value
    return validator


def VisitSchema(request, patient, visit=None):
    lz = get_localizer(request)
    return Schema({
        Required('cycle_ids'): All(
            [All(Coerce(int), validate_visit_cycle(request, patient, visit))],
            Length(
                min=1,
                msg=lz.translate(_(u'Must select at least one cycle')))),
        Required('visit_date'): Date(),
        Optional('add_forms'): bool
        })
