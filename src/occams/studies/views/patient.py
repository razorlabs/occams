from datetime import datetime

from pyramid.httpexceptions import HTTPBadRequest, HTTPFound, HTTPForbidden
from pyramid.session import check_csrf_token
from pyramid.view import view_config
import six
import sqlalchemy as sa
from sqlalchemy import orm
import wtforms
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.ext.dateutil.fields import DateField

from occams.roster import generate
from occams.forms.renderers import \
    make_form, render_form, apply_data, entity_data

from .. import _, models, Session
from ..utils import wtferrors, ModelField
from . import (
    site as site_views,
    enrollment as enrollment_views,
    form as form_views,
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

    # TODO: Need to limit PHI
    return {
        'phi': get_phi_entities(context, request),
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

    is_new = isinstance(context, models.PatientFactory)
    form = PatientSchema(context, request).from_json(request.json_body)

    if not form.validate():
        raise HTTPBadRequest(json={'errors': wtferrors(form)})

    if is_new:
        # if any errors occurr after this, this PID is essentially wasted
        patient = models.Patient(pid=generate(form.site.data.name))
        Session.add(patient)
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

    # Add the patient forms
    if is_new:
        schemata_query = (
            Session.query(models.Schema)
            .join(models.patient_schema_table))
        for schema in schemata_query:
            patient.entities.add(models.Entity(schema=schema))

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


@view_config(
    route_name='patient_forms',
    permission='view',
    renderer='../templates/patient/forms.pt')
def forms(context, request):
    patient = context.__parent__

    # XXX: no time for simplicty, gotta deliver...

    entities_query = (
        Session.query(models.Entity)
        .join(models.Context)
        .filter(models.Context.external == 'patient')
        .filter(models.Context.key == patient.id)
        .join(models.Schema)
        # Do not show PHI forms since there are dedicated tabs for them
        .filter(~models.Schema.id.in_(
            Session.query(models.patient_schema_table.c.schema_id)
            .subquery()))
        .order_by(models.Schema.name, models.Entity.collect_date))

    entities_count = entities_query.count()

    return {
        'phi': get_phi_entities(patient, request),
        'patient': view_json(patient, request),
        'entities': entities_query,
        'entities_count': entities_count,
    }


@view_config(
    route_name='patient_form',
    xhr=True,
    permission='view',
    renderer='string')
def form_ajax(context, request):
    version = request.GET.get('version')
    if not version:
        raise HTTPBadRequest()
    if version == context.schema.publish_date.isoformat():
        data = entity_data(context)
        schema = context.schema
    else:
        schema = (
            Session.query(models.Schema)
            .filter_by(name=context.schema.name, publish_date=version)
            .one())
        data = None
    Form = make_form(Session, schema, enable_metadata=False)
    form = Form(request.POST, data=data)
    return render_form(form)


@view_config(
    route_name='patient_form',
    permission='view',
    renderer='../templates/patient/form.pt')
def form(context, request):
    patient = context.__parent__.__parent__
    schema = context.schema

    (is_phi,) = (
        Session.query(
            Session.query(models.patient_schema_table)
            .filter_by(schema_id=schema.id)
            .exists())
        .one())
    if not is_phi:
        cancel_url = request.current_route_path(_route_name='patient_forms')
        enable_metadata = True
        # We cannot determine which study this form will be applied to
        # so just use any version from active studies
        available_schemata = (
            Session.query(models.Schema)
            .join(models.study_schema_table)
            .join(models.Study)
            .filter(models.Schema.publish_date != sa.null())
            .filter(models.Schema.retract_date == sa.null())
            .filter(models.Study.start_date != sa.null()))
        allowed_versions = sorted(set(
            s.publish_date for s in available_schemata))
    else:
        cancel_url = request.current_route_path(_route_name='patient')
        enable_metadata = False
        allowed_versions = None

    # Determine if there was a version change so we render the correct form
    if 'ofmetadata_-version' in request.POST:
        schema = (
            Session.query(models.Schema)
            .filter_by(
                name=context.schema.name,
                publish_date=request.POST['ofmetadata_-version'])
            .one())
    else:
        schema = context.schema

    Form = make_form(
        Session,
        schema,
        enable_metadata=enable_metadata,
        allowed_versions=allowed_versions)
    form = Form(request.POST, data=entity_data(context))

    if request.method == 'POST':
        if not request.has_permission('edit', context):
            raise HTTPForbidden()
        if form.validate():
            upload_dir = request.registry.settings['app.blob.dir']
            apply_data(Session, context, form.data, upload_dir)
            Session.flush()
            request.session.flash(_(u'Changes saved'), 'success')
            return HTTPFound(location=request.current_route_path())

    form_id = 'patient-form'
    return {
        'cancel_url': cancel_url,
        'phi': get_phi_entities(patient, request),
        'patient': view_json(patient, request),
        'form_id': form_id,
        'schema': context.schema,
        'entity': context,
        'form': render_form(form, attr={
            'id': form_id,
            'method': 'POST',
            'action': request.current_route_path(),
            'role': 'form'
        }),
    }


@view_config(
    route_name='patient_forms',
    xhr=True,
    permission='add',
    request_method='POST',
    renderer='json')
def form_add_json(context, request):
    check_csrf_token(request)

    def check_study_form(form, field):
        query = (
            Session.query(models.Schema)
            .join(models.study_schema_table)
            .join(models.Study)
            .filter(models.Study.start_date != sa.null())
            .filter(models.Schema.id == field.data.id))
        (exists,) = Session.query(query.exists()).one()
        if not exists:
            raise wtforms.ValidationError(request.localizer.translate(
                _(u'This form is not assosiated with a study')))

    class AddForm(wtforms.Form):
        schema = ModelField(
            session=Session,
            class_=models.Schema,
            validators=[
                wtforms.validators.InputRequired(),
                check_study_form])
        collect_date = DateField(
            validators=[wtforms.validators.InputRequired()])

    form = AddForm.from_json(request.json_body)

    if not form.validate():
        raise HTTPBadRequest(json={'errors': wtferrors(form)})

    default_state = (
        Session.query(models.State)
        .filter_by(name='pending-entry')
        .one())

    entity = models.Entity(
        schema=form.schema.data,
        collect_date=form.collect_date.data,
        state=default_state)
    context.__parent__.entities.add(entity)

    Session.flush()

    request.session.flash(
        _('Successfully added new ${form}',
            mapping={'form': entity.schema.title}),
        'success')

    return {
        '__next__': request.current_route_path(
            _route_name='patient_form', form=entity.id)
    }


@view_config(
    route_name='patient_forms',
    permission='edit',
    xhr=True,
    request_param='vocabulary=available_schemata',
    renderer='json')
@view_config(
    route_name='patient_form',
    permission='edit',
    xhr=True,
    request_param='vocabulary=available_schemata',
    renderer='json')
def available_schemata(context, request):
    """
    Returns a listing of available schemata for the study

    The results will try to exclude schemata configured for patients,
    or schemata that is currently used by the context study (if editing).

    GET parameters:
        term -- (optional) filters by schema title or publish date
        schema -- (optional) only shows results for specific schema name
                  (useful for searching for a schema's publish dates)
        grouped -- (optional) groups all results by schema name
    """

    class SearchForm(wtforms.Form):
        term = wtforms.StringField()
        schema = wtforms.StringField()
        grouped = wtforms.BooleanField()

    form = SearchForm(request.GET)
    form.validate()

    query = (
        Session.query(models.Schema)
        # only allow forms that are available to active studies
        .join(models.study_schema_table)
        .join(models.Study)
        .filter(models.Study.start_date != sa.null()))

    if form.schema.data:
        query = query.filter(models.Schema.name == form.schema.data)

    if form.term.data:
        wildcard = u'%' + form.term.data + u'%'
        query = query.filter(
            models.Schema.title.ilike(wildcard)
            | sa.cast(models.Schema.publish_date, sa.Unicode).ilike(wildcard))

    query = (
        query.order_by(
            models.Schema.title,
            models.Schema.publish_date.asc())
        .limit(100))

    return {
        '__query__': form.data,
        'schemata': (form_views.form2json(query)
                     if form.grouped.data
                     else [form_views.version2json(i) for i in query])
    }


def get_phi_entities(context, request):
    return (
        Session.query(models.Entity)
        .join(models.Context)
        .filter(models.Context.external == u'patient')
        .filter(models.Context.key == context.id)
        .join(models.Entity.schema)
        .join(models.patient_schema_table)
        .order_by(models.Schema.title))


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
