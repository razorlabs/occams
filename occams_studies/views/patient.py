from collections import OrderedDict
from datetime import datetime

from pyramid.httpexceptions import \
    HTTPBadRequest, HTTPFound, HTTPForbidden, HTTPOk
from pyramid.session import check_csrf_token
from pyramid.view import view_config
import six
import sqlalchemy as sa
from sqlalchemy import orm
import wtforms
from zope.sqlalchemy import mark_changed

from occams.utils.forms import wtferrors, ModelField
from occams_roster import generate
from occams_forms.renderers import \
    make_form, render_form, apply_data, entity_data, \
    form2json

from .. import _, models, Session
from . import (
    site as site_views,
    enrollment as enrollment_views,
    visit as visit_views,
    reference_type as reference_type_views,
    study as study_views,
    form as form_views)


@view_config(
    route_name='studies.patients',
    permission='view',
    renderer='../templates/patient/search.pt')
def search_view(context, request):
    """
    Generates data for the search result listing web view.
    """
    sites = [
        site
        for site in Session.query(models.Site).order_by(models.Site.title)
        if request.has_permission('view', site)]

    return {
        'sites': sites,
        'sites_count': len(sites),
        'results': search_json(context, request)
        }


@view_config(
    route_name='studies.patients',
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
            validators=[wtforms.validators.Optional()],
            filters=[lambda v: v.strip()[:100] if v else None])
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
        wildcard = u'%{}%'.format(form.query.data)
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
    route_name='studies.patient',
    permission='view',
    request_method='GET',
    renderer='../templates/patient/view.pt')
def view(context, request):

    # Keep track of recently viewed
    viewed = request.session.setdefault('viewed', OrderedDict())
    # Pop and re-enter data to maintain FIFO
    try:
        del viewed[context.pid]
    except KeyError:
        pass
    finally:
        viewed[context.pid] = {'pid': context.pid, 'view_date': datetime.now()}
    # Tidy up the queue, we don't want it to get too big, (uses FIFO)
    while len(viewed) > 10:
        viewed.popitem(last=False)
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
        'is_lab_enabled': Session.bind.has_table('specimen')
        }


@view_config(
    route_name='studies.patient',
    permission='edit',
    xhr=True,
    request_param='vocabulary=available_studies',
    renderer='json')
def available_studies(context, request):
    """
    Returns a list of studies that the patient can participate in
    """
    query = (
        Session.query(models.Study)
        .filter(models.Study.start_date != sa.null()))

    if 'term' in request.GET:
        wildcard = u'%' + request.GET['term'] + u'%'
        query = query.filter(models.Study.title.ilike(wildcard))

    query = query.order_by(models.Study.title)

    return {
        '__query__': request.GET.mixed(),
        'studies': [
            study_views.view_json(study, request, deep=False)
            for study in query]
    }


@view_config(
    route_name='studies.patient',
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
        '__url__': request.route_path('studies.patient', patient=patient.pid),
        'id': patient.id,
        'pid': patient.pid,
        'site': site_views.view_json(patient.site, request),
        'references': [{
            'reference_type': reference_type_views.view_json(
                reference.reference_type,
                request),
            'reference_number': reference.reference_number
            } for reference in references_query],
        'create_date': patient.create_date.isoformat(),
        'modify_date': patient.modify_date.isoformat()
        }


@view_config(
    route_name='studies.patients_forms',
    permission='admin',
    xhr=True,
    renderer='json')
def forms_list_json(context, request):
    """
    Returns a listing of available patient forms
    """
    query = (
        Session.query(models.Schema)
        .join(models.patient_schema_table)
        .order_by(
            models.Schema.name,
            models.Schema.publish_date))

    return {
        'forms': [form2json(s) for s in query]
    }


@view_config(
    route_name='studies.patients_forms',
    permission='admin',
    request_method='POST',
    xhr=True,
    renderer='json')
def forms_add_json(context, request):
    """
    Updates the available patient forms
    """
    check_csrf_token(request)

    def check_not_study_form(form, field):
        studies = (
            Session.query(models.Study)
            .filter(models.Study.schemata.any(id=field.data.id))
            .order_by(models.Study.title)
            .all())
        if studies:
            raise wtforms.ValidationError(request.localizer.translate(
                _(u'This form is already used by: {studies}'),
                mapping={'studies': ', '.join(s.title for s in studies)}))

    def check_not_termination_form(form, field):
        studies = (
            Session.query(models.Study)
            .filter(models.Study.termination_schema.has(name=field.data.name))
            .order_by(models.Study.title)
            .all())
        if studies:
            raise wtforms.ValidationError(request.localizer.translate(
                _(u'This form is already a termination form for: {studies}'),
                mapping={'studies': ', '.join(s.title for s in studies)}))

    def check_not_randomization_form(form, field):
        studies = (
            Session.query(models.Study)
            .filter(models.Study.randomization_schema.has(
                name=field.data.name))
            .order_by(models.Study.title)
            .all())
        if studies:
            raise wtforms.ValidationError(request.localizer.translate(
                _(u'This form is already a randomization form for: {studies}'),
                mapping={'studies': ', '.join(s.title for s in studies)}))

    def check_unique_form(form, field):
        exists = (
            Session.query(sa.literal(True))
            .filter(
                Session.query(models.Schema)
                .join(models.patient_schema_table)
                .filter(models.Schema.name == field.data.name)
                .exists())
            .scalar())
        if exists:
            raise wtforms.ValidationError(request.localizer.translate(
                _(u'Only a single version of forms are currently supported')))

    class AddForm(wtforms.Form):
        form = ModelField(
            session=Session,
            class_=models.Schema,
            validators=[
                wtforms.validators.InputRequired(),
                check_not_study_form,
                check_not_randomization_form,
                check_not_termination_form,
                check_unique_form])

    form = AddForm.from_json(request.json_body)

    if not form.validate():
        raise HTTPBadRequest(json={'errors': wtferrors(form)})

    Session.execute(
        models.patient_schema_table.insert()
        .values(schema_id=form.form.data.id))

    mark_changed(Session())

    return form2json(form.form.data)


@view_config(
    route_name='studies.patients_forms',
    permission='admin',
    request_method='DELETE',
    xhr=True,
    renderer='json')
def forms_delete_json(context, request):
    """
    Removes a required patient form.
    """
    check_csrf_token(request)

    def check_not_has_data(form, field):
        (exists,) = (
            Session.query(
                Session.query(models.Entity)
                .filter_by(schema=field.data)
                .exists())
            .one())
        if exists:
            raise wtforms.ValidationError(request.localizer.translate(
                _(u'Unable to remove because data has already been entered')))

    class DeleteForm(wtforms.Form):
        form = ModelField(
            session=Session,
            class_=models.Schema,
            validators=[
                wtforms.validators.InputRequired(),
                check_not_has_data])

    form = DeleteForm.from_json(request.json_body)

    if not form.validate():
        raise HTTPBadRequest(body='<br />'.join(form.form.errors))

    Session.execute(
        models.patient_schema_table.delete()
        .where(models.patient_schema_table.c.schema_id == form.form.data.id))

    mark_changed(Session())

    return HTTPOk()


@view_config(
    route_name='studies.patients',
    permission='add',
    xhr=True,
    request_method='POST',
    renderer='json')
@view_config(
    route_name='studies.patient',
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
    route_name='studies.patient',
    permission='delete',
    xhr=True,
    request_method='DELETE',
    renderer='json')
def delete_json(context, request):
    check_csrf_token(request)
    patient = context
    Session.delete(patient)
    Session.flush()

    del request.session.setdefault('viewed', OrderedDict())[context.pid]
    request.session.changed()

    msg = request.localizer.translate(
        _('Patient ${pid} was successfully removed'),
        mapping={'pid': patient.pid})
    request.session.flash(msg, 'success')
    return {'__next__': request.current_route_path(_route_name='studies.main')}


@view_config(
    route_name='studies.patient_forms',
    permission='view',
    renderer='../templates/patient/forms.pt')
def forms(context, request):
    patient = context.__parent__
    return {
        'phi': get_phi_entities(patient, request),
        'patient': view_json(patient, request),
        'entities': form_views.list_json(context, request)['entities']
    }


@view_config(
    route_name='studies.patient_form',
    permission='view',
    renderer='../templates/patient/form.pt')
def form(context, request):
    """
    XXX: Cannot merge into single view
        because of the way patient forms are handled
    """

    patient = context.__parent__.__parent__
    schema = context.schema

    (is_phi,) = (
        Session.query(
            Session.query(models.patient_schema_table)
            .filter_by(schema_id=schema.id)
            .exists())
        .one())
    if not is_phi:
        cancel_url = request.current_route_path(_route_name='studies.patient_forms')
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
        cancel_url = request.current_route_path(_route_name='studies.patient')
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
        # Only validate if the dependent field is valid
        if not form.reference_type.errors and not type_.check(number):
            raise wtforms.ValidationError(request.localizer.translate(
                _(u'Invalid format')))

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
            raise wtforms.ValidationError(request.localizer.translate(
                _(u'Already assigned')))

    def check_allowed(form, field):
        if not request.has_permission('view', field.data):
            raise wtforms.ValidationError(request.localizer.translate(
                _(u'You do not belong to this site')))

    class ReferenceForm(wtforms.Form):
        reference_type = ModelField(
            session=Session,
            class_=models.ReferenceType,
            validators=[
                wtforms.validators.InputRequired()])
        reference_number = wtforms.StringField(
            validators=[
                wtforms.validators.InputRequired(),
                check_reference_format,
                check_unique_reference])

    class PatientForm(wtforms.Form):
        site = ModelField(
            session=Session,
            class_=models.Site,
            validators=[
                wtforms.validators.InputRequired(),
                check_allowed])
        references = wtforms.FieldList(wtforms.FormField(ReferenceForm))

    return PatientForm
