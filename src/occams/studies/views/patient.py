from datetime import datetime

from pyramid.httpexceptions import HTTPBadRequest
from pyramid.session import check_csrf_token
from pyramid.view import view_config
import six
import sqlalchemy as sa
from sqlalchemy import orm
from voluptuous import *  # NOQA

from occams.roster import generate

from .. import _, models, Session
from . import enrollment as enrollment_views, visit as visit_views
from ..validators import DatabaseEntry


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
            Coerce(six.binary_types),
            lambda v: v.strip(),
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

    sites_query = Session.query(models.Site).order_by(models.Site.title)

    return {
        'available_sites': [
            s for s in sites_query if request.has_permission('view', s)],
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
            context['visits'], request)['visits'],
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
    Session.delete(patient)
    Session.flush()
    msg = request.localizer.translate(
        _('Patient ${pid} was successfully removed'),
        mapping={'pid': patient.pid})
    request.session.flash(msg, 'success')
    return {'__next__': request.current_route_path(_route_name='home')}


def PatientSchema(context, request):
    """
    Declares data format expected for managing patient properties
    """

    def check_can_view_site(value):
        if not request.has_permission('view', value):
            raise Invalid(request.localizer.translate(
                _(u'You do not have access to {site}'),
                mapping={'site': value.title}))
        return value

    def check_reference_format(value):
        if not value['reference_type'].check(value['reference_number']):
            msg = request.localizer.translate(
                _(u'${type} ${number} is not a valid format'),
                mapping={
                    'type': value['reference_type'].title,
                    'number': value['reference_number']})
            raise Invalid(msg, path=['reference_number'])
        return value

    def check_unique_reference(value):
        query = (
            Session.query(models.PatientReference)
            .filter_by(
                reference_type=value['reference_type'],
                reference_number=value['reference_number']))
        if isinstance(context, models.Patient):
            query = query.filter(models.PatientReference.patient != context)
        reference = query.first()
        if reference:
            # Need to translate before sending back to client
            msg = request.localizer.translate(
                _(u'${type} ${number} is already assigned to ${pid}'),
                mapping={
                    'type': reference.reference_type.title,
                    'number': reference.reference_number,
                    'pid': reference.patient.pid})
            raise Invalid(msg, path=['reference_number'])
        return value

    return Schema({
        Required('site'): All(
            DatabaseEntry(
                models.Site,
                msg=_(u'Site does not exist'),
                localizer=request.localizer),
            check_can_view_site),
        Required('references', default=[]): [All({
            Required('reference_type'): DatabaseEntry(
                models.ReferenceType,
                msg=_(u'Reference type does not exist'),
                localizer=request.localizer),
            Required('reference_number'): Coerce(six.binary_type),
            Extra: object
            },
            check_reference_format,
            check_unique_reference,
            )],
        Extra: object
        })
