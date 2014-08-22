from datetime import datetime
from pyramid.httpexceptions import HTTPBadRequest, HTTPNotFound
from pyramid.i18n import get_localizer
from pyramid.session import check_csrf_token
from pyramid.view import view_config
import six
from sqlalchemy import orm
from voluptuous import *  # NOQA

from occams.roster import generate

from .. import _, models, Session
from .enrollment import get_enrollments_data
from .visit import get_visits_data


@view_config(
    route_name='patients',
    permission='patient_view',
    renderer='../templates/patient/search.pt')
@view_config(
    route_name='patients',
    permission='patient_view',
    xhr=True,
    renderer='json')
def search(request):
    """
    Searches for a patient based on their reference numbers
    """

    schema = Schema({
        Required('query', default=''): All(
            Coearce(lambda v: v and str(v).strip()),
            # Avoid gigantic queries
            Length(max=100)),
        Required('offset', default=0): All(Coerce(int), Clamp(min=0)),
        Required('limit', default=25): All(
            Coerce(int), Clamp(min=0, max=50), Any(10, 25, 50)),
        Extra: object,
        })

    search = schema(request.GET)

    query = Session.query(models.Patient)

    if search['query']:
        wildcard = '%{0}%'.format(search['query'])
        query = (
            Session.query(models.Patient)
            .outerjoin(models.Patient.enrollments)
            .outerjoin(models.Patient.strata)
            .outerjoin(models.Patient.reference_numbers)
            .filter(
                models.Patient.pid.ilike(wildcard)
                | models.Enrollment.reference_number.ilike(wildcard)
                | models.Stratum.reference_number.ilike(wildcard)
                | models.PatientReference.reference_number.ilike(wildcard)))

    # TODO include only those the user is a site member of

    previous_search = request.session.get(request.matched_route.name)

    if previous_search:
        previous_search, last_pid = previous_search
        if previous_search == search:
            query.filter(models.Patient.pid >= last_pid)

    query = (
        query
        .order_by(models.Patient.pid.asc())
        .offset(search['offset'])
        .limit(search['limit']))

    results = [get_patient_data(p) for p in query
               if request.has_permission('patient_view', p.site)]

    request.session[request.matched_route.name] = (search, results[-1]['pid'])

    return {'results': results}


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
    route_name='patients',
    permission='patient_add',
    xhr=True,
    request_method='POST',
    renderer='json')
def add_json(request):
    check_csrf_token(request)
    schema = PatientSchema(request, patient)
    try:
        data = schema(request.json_body)
    except MultipleInvalid as exc:
        raise HTTPBadRequest(json={
            'validation_errors': [e.error_message for e in exc.errors]})
    site = Session.query(models.Site).get(data['site_id'])
    pid = generate(site.name)
    patient = models.Patient(pid=pid)
    apply_changes(patient, data)
    return get_patient_data(request, patient)


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
            'validation_errors': [e.error_message for e in exc.errors]})
    apply_changes(patient, data)
    return get_patient_data(request, patient)


@view_config(
    route_name='patient',
    permission='petient_delete',
    xhr=True,
    request_method='DELETE',
    renderer='json')
def delete_json(request):
    check_csrf_token(request)
    patient = get_patient(request)
    lz = get_localizer(request)
    Session.delete(patient)
    Session.flush()
    msg = lz.translate(
        _('Patient ${pid} was successfully removed'),
        mapping={'pid': patient.pid})
    request.session.flash(msg, 'success')
    return {'__next__': request.current_route_path(_route_name='home')}


def validate_reference(request, patient):
    """
    Returns a validator callback that checks the reference data
    """
    def validator(value):
        lz = get_localizer(request)

        type_ = (
            Session.query(models.ReferenceType)
            .get(value['reference_type_id']))
        number = value['reference_number']
        if not type_.check_reference_number(number):
            msg = lz.translate(
                _(u'${type} ${number} is not a valid format'),
                mapping={'type': type_.title, 'number': number})
            raise Invalid(msg, path=['reference_number'])

        reference_query = (
            Session.query(models.PatientReference)
            .filter_by(reference_type=type_, reference_number=number)
            .filter(models.PatientReference.patient != patient))
        reference = reference_query.first()
        if reference:
            # Need to translate before sending back to client
            msg = lz.translate(
                _(u'${type} ${number} is already assigned to ${pid}'),
                mapping={
                    'type': reference.reference_type.title,
                    'number': reference.reference_number,
                    'pid': reference.patient.pid})
            raise Invalid(msg, path=['reference_number'])

        return value
    return validator


def PatientSchema(request, patient):
    valid_sites = [s.id for s in get_available_sites(request)]
    valid_types = [r.id for r in Session.query(models.ReferenceType)]
    lz = get_localizer(request)
    return Schema({
        Required('site_id', default=patient.site.id): All(
            Coerce(int),
            Any(*valid_sites, msg=lz.translate(_(u'Invalid site')))
            ),
        Required('references', default=[]): [All({
            Required('reference_type_id'): All(
                Coerce(int),
                Any(*valid_types, msg=lz.translate(_(u'Invalid type')))
            ),
            Required('reference_number'): Coerce(lambda v: six.u(str(v))),
            Extra: object
            }, validate_reference(request, patient))],
        Extra: object
        })


def apply_changes(patient, data):
    patient.site = Session.query(models.Site).get(data['site_id'])
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
            type_ = Session.query(models.ReferenceType).get(reference_type_id)
            patient.references.append(models.PatientReference(
                reference_type=type_,
                reference_number=reference_number))

    Session.flush()
    return patient


def get_patient_data(request, patient):
    references_query = (
        Session.query(models.PatientReference)
        .filter_by(patient=patient)
        .join(models.PatientReference.reference_type)
        .options(orm.joinedload(models.PatientReference.reference_type))
        .order_by(models.ReferenceType.title.asc()))
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
            } for r in references_query]
        }


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
    """
    Rertuns a list of sites that the user has access to
    """
    sites_query = Session.query(models.Site).order_by(models.Site.title)
    return \
        [s for s in sites_query if request.has_permission('site_view', s)]
