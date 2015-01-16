from datetime import datetime

from pyramid.httpexceptions import HTTPBadRequest, HTTPFound
from pyramid.session import check_csrf_token
from pyramid.view import view_config
import six
import sqlalchemy as sa
from sqlalchemy import orm
import wtforms
from wtforms.ext.sqlalchemy.fields import QuerySelectField

from occams.roster import generate

from .. import _, models, Session
from ..utils import wtferrors
from . import (
    site as site_views,
    enrollment as enrollment_views,
    visit as visit_views,
    reference_type as reference_type_views)


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

    class SearchForm(wtforms.Form):
        query = wtforms.StringField(
            validators=[
                wtforms.validators.Optional(),
                wtforms.validators.Length(max=100)],
            filters=[lambda v: v.strip()])
        page = wtforms.IntegerField(
            validators=[wtforms.validators.Optional()],
            filters=[lambda v: 1 if not v or v < 1 else v],
            default=1)

    form = SearchForm(request.GET)
    form.validate()

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

    if form.query.data:
        wildcard = '%{0}%'.format(form.query.data)
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
        .offset((form.page.data - 1) * per_page)
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
        '__has_previous__': form.page.data > 1,
        '__has_next__': len(patients) > per_page,
        '__page__': form.page.data,
        '__query__': form.query.data,
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
        'site': site_views.view_json(patient.site, request),
        'references': [{
            'reference_type': reference_type_views.view_json(
                reference.reference_type,
                request),
            'reference_number': reference.reference_number
            } for reference in references_query],
        }


@view_config(
    route_name='patients_forms',
    permission='admin',
    xhr=True,
    renderer='json')
def forms_list_json(context, request):
    """
    Returns a listing of available patient forms
    """
    return {
        'forms': []
    }


@view_config(
    route_name='patients_forms',
    permission='admin',
    request_method='POST',
    xhr=True,
    renderer='json')
def forms_edit_json(context, request):
    """
    Updates the available patient forms
    """
    return {}


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

    form = PatientSchema(context, request).from_json(request.json_body)

    if not form.validate():
        raise HTTPBadRequest(json={'errors': wtferrors(form)})

    if isinstance(context, models.PatientFactory):
        pid = generate(form.site.data.name)
        patient = models.Patient(pid=pid)
    else:
        patient = context

    patient.site = form.site.data

    if form.references.data:
        inputs = dict(
            ((r['reference_type'].id, r['reference_number']), r)
            for r in form.references.data)

        for r in patient.references:
            try:
                # Remove already-existing values from the inputs
                del inputs[(r.reference_type.id, r.reference_number)]
            except KeyError:
                # References not in the inputs indicate they have been removed
                Session.delete(r)

        for r in six.itervalues(inputs):
            Session.add(models.PatientReference(
                patient=patient,
                reference_type=r['reference_type'],
                reference_number=r['reference_number']))

    Session.flush()
    Session.refresh(patient)

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

    def check_reference_format(form, field):
        type_ = form.reference_type.data
        number = form.reference_number.data
        if not type_.check(number):
            raise wtforms.ValidationError(request.localizer.translate(_(
                _(u'Invalid format'))))

    def check_unique_reference(form, field):
        type_ = form.reference_type.data
        number = form.reference_number.data
        query = (
            Session.query(models.PatientReference)
            .filter_by(reference_type=type_, reference_number=number))
        if isinstance(context, models.Patient):
            query = query.filter(models.PatientReference.patient != context)
        ref = query.first()
        if ref:
            raise wtforms.ValidationError(request.localizer.translate(_(
                u'Already in use.')))

    def available_reference_types():
        return Session.query(models.ReferenceType).order_by('title')

    def available_sites():
        allowed_site_ids = [
            s.id
            for s in Session.query(models.Site).order_by('title')
            if request.has_permission('view', s)]
        return (
            Session.query(models.Site)
            .filter(models.Site.id.in_(allowed_site_ids))
            .order_by('title'))

    class ReferenceForm(wtforms.Form):
        reference_type = QuerySelectField(
            query_factory=available_reference_types,
            get_label='title',
            validators=[
                wtforms.validators.InputRequired()])
        reference_number = wtforms.StringField(
            validators=[
                wtforms.validators.InputRequired(),
                check_reference_format,
                check_unique_reference])

    class PatientForm(wtforms.Form):
        site = QuerySelectField(
            query_factory=available_sites,
            get_label='title',
            validators=[wtforms.validators.InputRequired()])
        references = wtforms.FieldList(wtforms.FormField(ReferenceForm))

    return PatientForm
