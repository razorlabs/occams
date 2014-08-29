from datetime import datetime

from pyramid.httpexceptions import HTTPBadRequest
from pyramid.i18n import get_localizer
from pyramid.session import check_csrf_token
from pyramid.view import view_config
import six
import sqlalchemy as sa
from sqlalchemy import orm
from voluptuous import *  # NOQA

from occams.roster import generate

from .. import _, models, Session
from . import (
    enrollment as enrollment_views,
    site as site_views,
    visit as visit_views)


@view_config(
    route_name='patients',
    permission='view',
    renderer='../templates/patient/search.pt')
@view_config(
    route_name='patients',
    permission='view',
    xhr=True,
    renderer='json')
def search_json(context, request):
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
    permission='view',
    request_method='GET',
    renderer='../templates/patient/view.pt')
def view(context, request):
    patient = request.context
    request.session.setdefault('viewed', {})
    request.session['viewed'][patient.pid] = {
        'pid': patient.pid,
        'view_date': datetime.now()
    }
    request.session.changed()
    return {
        'available_sites': site_views.list_(None, request)['sites'],
        'available_reference_types': (
            Session.query(models.ReferenceType)
            .order_by(models.ReferenceType.title.asc())),
        'available_studies': (
            Session.query(models.Study)
            .filter(models.Study.start_date != sa.sql.null())
            .order_by(models.Study.title.asc())),
        'patient': view_json(context, request),
        'enrollments': enrollment_views.list_json(
            context['enrollments'], request)['enrollments'],
        'visits': visit_views.list_json(
            context['visits'], request, summary=True)['visits'],
        }


@view_config(
    route_name='patient',
    permission='view',
    request_method='GET',
    xhr=True,
    renderer='json')
def view_json(context, request):
    patient = context
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


@view_config(
    route_name='patients',
    permission='add',
    xhr=True,
    request_method='POST',
    renderer='json')
@view_config(
    route_name='patient',
    permission='edit',
    xhr=True,
    request_method='PUT',
    renderer='json')
def edit_json(context, request):
    check_csrf_token(request)

    schema = PatientSchema(context, request)
    patient = context if isinstance(context, models.Patient) else None

    try:
        data = schema(request.json_body)
    except MultipleInvalid as exc:
        raise HTTPBadRequest(json={
            'validation_errors': [e.error_message for e in exc.errors]})

    if isinstance(context, models.PatientFactory):
        pid = generate(data['site'].name)
        patient = models.Patient(pid=pid)

    patient.site = data['site']

    if data['references']:
        incoming = dict([((r['reference_type'].id, r['reference_number']), r)
                        for r in data['references']])
        # make a copy of the list so we can remove from the original
        current = [r for r in patient.references]
        for r in current:
            key = (r.reference_type_id, r.reference_number)
            if key not in incoming:
                patient.references.remove(r)
            else:
                del incoming[key]

        for value in six.itervalues(incoming):
            patient.references.append(models.PatientReference(
                reference_type=value['reference_type'],
                reference_number=value['reference_number']))

    Session.flush()

    return view_json(patient, request)


@view_config(
    route_name='patient',
    permission='delete',
    xhr=True,
    request_method='DELETE',
    renderer='json')
def delete_json(context, request):
    check_csrf_token(request)
    patient = context
    lz = get_localizer(request)
    Session.delete(patient)
    Session.flush()
    msg = lz.translate(
        _('Patient ${pid} was successfully removed'),
        mapping={'pid': patient.pid})
    request.session.flash(msg, 'success')
    return {'__next__': request.current_route_path(_route_name='home')}


def PatientSchema(context, request):
    """
    Declares data format expected for managing patient properties
    """

    return Schema({
        Required('site'): All(Coerce(int), coerce_site(context, request)),
        Required('references', default=[]): [All({
            Required('reference_type'): All(
                Coerce(int), coerce_reference_type(context, request)),
            Required('reference_number'): Coerce(str),
            Extra: object
            },
            check_reference_format(context, request),
            check_unique_reference(context, request),
            )],
        Extra: object
        })


def check_reference_format(context, request):
    """
    Returns a validator that checks number with the pattern the type expects
    """
    def validator(value):
        lz = get_localizer(request)
        type_ = value['reference_type']
        number = value['reference_number']
        if not type_.check_reference_number(number):
            msg = lz.translate(
                _(u'${type} ${number} is not a valid format'),
                mapping={'type': type_.title, 'number': number})
            raise Invalid(msg, path=['reference_number'])
        return value
    return validator


def check_unique_reference(context, request):
    """
    Returns a validator that checks the reference number is not already taken
    """
    def validator(value):
        lz = get_localizer(request)

        reference_query = (
            Session.query(models.PatientReference)
            .filter_by(
                reference_type=value['reference_type'],
                reference_number=value['reference_number']))

        if isinstance(context, models.Patient):
            reference_query = (
                reference_query
                .filter(models.PatientReference.patient != context))

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


def coerce_site(context, request):
    """
    Returns a validator to coerce a site id to a site object
    Also, checks if the user has access to use the site.
    """
    def validator(value):
        lz = get_localizer(request)
        study = Session.query(models.Site).get(value)
        if study is None:
            raise Invalid(lz.translate(_(u'Site does not exist')))
        if not request.has_permission('view', study):
            raise Invalid(lz.translate(
                _(u'You do not have access to {site}'),
                mapping={'site': study.title}))
        return study
    return validator


def coerce_reference_type(context, request):
    """
    Returns a validator to coerce a reference type id to a type object
    """
    def validator(value):
        lz = get_localizer(request)
        reftype = Session.query(models.ReferenceType).get(value)
        if reftype is None:
            raise Invalid(lz.translate(_(u'Reference type does not exist')))
        return reftype
    return validator
