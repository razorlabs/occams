from datetime import datetime

from good import *  # NOQA
from pyramid.httpexceptions import HTTPBadRequest, HTTPFound
from pyramid.session import check_csrf_token
from pyramid.view import view_config
import six
import sqlalchemy as sa
from sqlalchemy import orm

from occams.roster import generate

from .. import _, models, Session
from . import (
    site as site_views,
    enrollment as enrollment_views,
    visit as visit_views,
    reference_type as reference_type_views)
from ..validators import invalid2dict, Model, Key


@view_config(
    route_name='patients',
    permission='view',
    renderer='../templates/patient/search.pt')
def search_view(context, request):
    """
    Generates data for the search result listing web view.
    If the search only yields a single result, a redirect to the patient view
    will be returned.
    """
    results = search_json(context, request)
    if len(results['patients']) == 1:
        return HTTPFound(location=results['patients'][0]['__url__'])
    return {'results': results}


@view_config(
    route_name='patients',
    permission='view',
    xhr=True,
    renderer='json')
def search_json(context, request):
    """
    Generates a search result listing based on a string term.

    Expects the following GET paramters:
        query -- A partial patient reference string
        page -- The page to in the result listing to fetch (default: 1)

    Returns a JSON object containing the following properties:
        __has_next__ -- flag indicating there are more results to fetch
        __has_previous__ -- flag indicating that we're not in the first page
        __page__ -- the current "page" in the results
        __query__ -- the search query requested
        patients -- the result list, each record is patient JSON object.
                    see ``view_json`` for more info.
                    This object also contains an additional property:
                    __last_visit_date__ -- indicates the last interaction
                                           with the patient
    """
    per_page = 10

    schema = Schema({
        'query': Any(
            All(
                # If we get a string type, the coerce to unicode
                Type(*six.string_types),
                Coerce(six.text_type),
                lambda v: v.strip(),
                # Avoid gigantic queries
                Length(max=100)),
            Default(None)),
        'page': Any(All(Coerce(int), Clamp(min=1)), Default(1)),
        Extra: Remove,
        })

    data = schema(request.GET.mixed())

    # Only include sites that the user is a member of
    sites = Session.query(models.Site)
    site_ids = [s.id for s in sites if request.has_permission('view', s)]

    query = (
        Session.query(models.Patient)
        .options(orm.joinedload(models.Patient.site))
        .add_column(
            Session.query(models.Visit.visit_date)
            .filter(models.Visit.patient_id == models.Patient.id)
            .order_by(models.Visit.visit_date.desc())
            .limit(1)
            .as_scalar())
        .filter(models.Patient.site_id.in_(site_ids)))

    if data['query']:
        wildcard = '%{0}%'.format(data['query'])
        query = (
            query.filter(
                models.Patient.pid.ilike(wildcard)
                | models.Patient.enrollments.any(
                    models.Enrollment.reference_number.ilike(wildcard))
                | models.Patient.references.any(
                    models.PatientReference.reference_number.ilike(wildcard))))

    # TODO: There are better postgres-specific ways of doing pagination
    # https://coderwall.com/p/lkcaag
    # This method gets the number per page and one record after
    # to determine if there is more to view
    query = (
        query
        .order_by(models.Patient.pid.asc())
        .offset((data['page'] - 1) * per_page)
        .limit(per_page + 1))

    def process(result):
        patient, last_visit_date = result
        data = view_json(patient, request)
        data.update(enrollment_views.list_json(
            patient['enrollments'],
            request))
        data['__last_visit_date__'] = \
            last_visit_date and last_visit_date.isoformat()
        return data

    patients = [process(result) for result in query]

    return {
        '__has_previous__': data['page'] > 1,
        '__has_next__': len(patients) > per_page,
        '__page__': data['page'],
        '__query__': data['query'],
        'patients': patients[:per_page]
    }


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
        'pid': patient.pid,
        'site': site_views.view_json(patient.site, context),
        'references': [{
            'reference_type': reference_type_views.view_json(
                reference.reference_type,
                request),
            'reference_number': reference.reference_number
            } for reference in references_query],
        'create_date': patient.create_date.isoformat(),
        'modify_date': patient.modify_date.isoformat(),
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
    except Invalid as e:
        raise HTTPBadRequest(json={'errors': invalid2dict(e)})

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
            raise Invalid(request.localizer.translate(
                _(u'${type} ${number} is not a valid format'),
                mapping={
                    'type': value['reference_type'].title,
                    'number': value['reference_number']}))
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
            msg = request.localizer.translate(
                _(u'${type} ${number} is already assigned to ${pid}'),
                mapping={
                    'type': reference.reference_type.title,
                    'number': reference.reference_number,
                    'pid': reference.patient.pid})
            raise Invalid(msg)
        return value

    return Schema({
        'site': All(
            Any(Key('id'), int),
            Model(models.Site, localizer=request.localizer),
            check_can_view_site),
        'references': [All({
            'reference_type': All(
                Any(Key('id'), int),
                Model(models.ReferenceType, localizer=request.localizer)),
            'reference_number': All(
                Type(*six.string_types),
                Coerce(six.binary_type)),
            Extra: Remove
            },
            check_reference_format,
            check_unique_reference)],
        Extra: Remove
        })
