from datetime import datetime

from pyramid.httpexceptions import HTTPBadRequest, HTTPForbidden, HTTPFound
from pyramid.session import check_csrf_token
from pyramid.view import view_config
import sqlalchemy as sa
from sqlalchemy import orm
import wtforms
from wtforms.ext.dateutil.fields import DateField

from occams.utils.forms import wtferrors, ModelField, Form
from occams_forms.renderers import \
    make_form, render_form, apply_data, entity_data, modes

from .. import _, models, Session
from . import form as form_views


@view_config(
    route_name='studies.visits',
    permission='view',
    xhr=True,
    renderer='json')
def list_json(context, request):
    patient = context.__parent__

    visits_query = (
        Session.query(models.Visit)
        .options(
            orm.joinedload(models.Visit.cycles).joinedload(models.Cycle.study))
        .filter_by(patient=patient)
        .order_by(models.Visit.visit_date.desc()))

    return {
        'visits': [
            view_json(v, request) for v in visits_query]
        }


@view_config(
    route_name='studies.visit',
    permission='view',
    renderer='../templates/visit/view.pt')
def view(context, request):
    return {
        'visit': view_json(context, request),
        'is_lab_enabled': Session.bind.has_table('specimen')
        }


@view_config(
    route_name='studies.visit',
    permission='view',
    xhr=True,
    renderer='json')
def view_json(context, request):
    visit = context
    return {
        '__url__': request.route_path('studies.visit',
                                      patient=visit.patient.pid,
                                      visit=visit.visit_date.isoformat()),
        'id': visit.id,
        'cycles': [{
            'id': cycle.id,
            'study': {
                'id': cycle.study.id,
                'name': cycle.study.name,
                'title': cycle.study.title,
                'code': cycle.study.code
                },
            'name': cycle.name,
            'title': cycle.title,
            'week': cycle.week
            } for cycle in visit.cycles],
        'patient': {
            '__url__': request.route_path('studies.patient',
                                          patient=visit.patient.pid),
            'site': {
                'title': visit.patient.site.title,
                },
            'pid': visit.patient.pid
            },
        'visit_date': visit.visit_date.isoformat(),
        'entities': form_views.list_json(visit['forms'], request)['entities']
        }


@view_config(
    route_name='studies.visits_cycles',
    permission='view',
    xhr=True,
    renderer='json')
def cycles_json(context, request):
    """
    AJAX handler for cycle field options
    """
    data = {'cycles': []}

    query = (
        Session.query(models.Cycle)
        .join(models.Cycle.study))

    if 'ids' in request.GET:
        query = query.filter(models.Cycle.id.in_(
            list(map(int, request.GET.getall('ids')))))
    elif 'q' in request.GET:
        query = query.filter(
            models.Cycle.title.ilike(u'%%%s%%' % request.GET['q']))
    else:
        return data

    query = (
        query
        .order_by(models.Study.title, models.Cycle.week)
        .limit(25))

    data['cycles'] = [{
        'id': cycle.id,
        'title': cycle.title
        } for cycle in query]

    return data


@view_config(
    route_name='studies.visits',
    permission='view',
    request_method='GET',
    request_param='cycles',
    xhr=True,
    renderer='json')
@view_config(
    route_name='studies.visit',
    permission='view',
    request_method='GET',
    request_param='cycles',
    xhr=True,
    renderer='json')
def validate_cycles(context, request):
    """
    jQuery Validation callback
    GET parameters:
        cycles -- a comma delmited list of cycle ids
    """
    # Convert the select2 string delimited data into JSON
    field = 'cycles'
    raw = request.GET.getall(field)
    inputs = {field: [c for dc in raw for c in dc.split(',')]}
    form = VisitSchema(context, request).from_json(inputs)
    if not form.validate() and field in form.errors:
        # There doesn't seem to be a better way to send a delimited list
        # since jQueryValidation only accepts the error message...
        return '<br />'.join(e for es in form.errors[field] for e in es)
    else:
        return True


@view_config(
    route_name='studies.visits',
    permission='add',
    request_method='POST',
    xhr=True,
    renderer='json')
@view_config(
    route_name='studies.visit',
    permission='edit',
    request_method='PUT',
    xhr=True,
    renderer='json')
def edit_json(context, request):
    check_csrf_token(request)
    is_new = isinstance(context, models.VisitFactory)
    form = VisitSchema(context, request).from_json(request.json_body)

    if not form.validate():
        raise HTTPBadRequest(json={'errors': wtferrors(form)})

    if is_new:
        visit = models.Visit(patient=context.__parent__)
        Session.add(visit)
    else:
        visit = context

    visit.patient.modify_date = datetime.now()
    visit.visit_date = form.visit_date.data

    # Filter only new cycles and prune removed/existing cycles
    incoming_cycles = set(form.cycles.data)
    for cycle in visit.cycles:
        if cycle not in incoming_cycles:
            visit.cycles.remove(cycle)
        else:
            incoming_cycles.remove(cycle)
    visit.cycles.extend(list(incoming_cycles))

    # TODO: hard coded for now, will be removed when workflows are in place
    default_state = (
        Session.query(models.State)
        .filter_by(name='pending-entry').one())

    # Update collect date for those forms that were never modified
    if not is_new:
        for entity in visit.entities:
            if entity.state == default_state \
                    and entity.collect_date != visit.visit_date:
                entity.collect_date = visit.visit_date

    if form.include_forms.data:

        # find the most recent cycle form version relative to the visit
        recents = (
            Session.query(
                models.Schema.name.label('name'),
                sa.func.max(models.Schema.publish_date).label('publish_date'))
            .join(models.Cycle.schemata)
            .filter(models.Cycle.id.in_([c.id for c in visit.cycles]))
            .filter(models.Schema.publish_date <= visit.visit_date)
            .filter(models.Schema.retract_date == sa.null())
            .group_by(models.Schema.name)
            .subquery('max_version'))

        # retrive the full schema record of the previous find
        schemata_query = (
            Session.query(models.Schema)
            .join(recents, (
                (models.Schema.name == recents.c.name)
                & (models.Schema.publish_date == recents.c.publish_date))))

        # Ignore already-added schemata
        if isinstance(context, models.Visit) and visit.entities:
            schemata_query = schemata_query.filter(
                ~models.Schema.name.in_(
                    [entity.schema.name for entity in visit.entities]))

        for schema in schemata_query:
            entity = models.Entity(
                schema=schema,
                collect_date=visit.visit_date,
                state=default_state)
            visit.patient.entities.add(entity)
            visit.entities.add(entity)

    # Lab might not be enabled on a environments, check first
    if form.include_specimen.data and Session.bind.has_table('specimen'):
        from occams_lims import models as lab
        drawstate = (
            Session.query(lab.SpecimenState)
            .filter_by(name=u'pending-draw')
            .one())
        location_id = visit.patient.site.lab_location.id
        for cycle in visit.cycles:
            if cycle in incoming_cycles:
                for specimen_type in cycle.specimen_types:
                    Session.add(lab.Specimen(
                        patient=visit.patient,
                        cycle=cycle,
                        specimen_type=specimen_type,
                        state=drawstate,
                        collect_date=visit.visit_date,
                        location_id=location_id,
                        tubes=specimen_type.default_tubes))

    Session.flush()

    return view_json(visit, request)


@view_config(
    route_name='studies.visit',
    permission='delete',
    request_method='DELETE',
    renderer='json')
def delete_json(context, request):
    check_csrf_token(request)
    list(map(Session.delete, context.entities))
    context.patient.modify_date = datetime.now()
    Session.delete(context)
    Session.flush()
    request.session.flash(_(
        u'Sucessfully deleted ${visit_date}',
        mapping={'visit_date': context.visit_date}))
    return {'__next__': request.route_path('studies.patient',
                                           patient=context.patient.pid)}


@view_config(
    route_name='studies.visit_form',
    permission='view',
    renderer='../templates/visit/form.pt')
def form(context, request):
    """
    XXX: Cannot merge into single view
        because of the way patient forms are handled
    """

    visit = context.__parent__.__parent__
    allowed_schemata = (
        Session.query(models.Schema)
        .join(models.study_schema_table)
        .join(models.Study)
        .join(models.Cycle)
        .filter(models.Cycle.id.in_([cycle.id for cycle in visit.cycles])))
    allowed_versions = [s.publish_date for s in allowed_schemata]

    if request.has_permission('admin'):
        transition = modes.ALL
    elif request.has_permission('transition'):
        transition = modes.AVAILABLE
    else:
        transition = modes.AUTO

    Form = make_form(
        Session,
        context.schema,
        entity=context,
        show_metadata=True,
        transition=transition,
        allowed_versions=allowed_versions,
    )

    form = Form(request.POST, data=entity_data(context))

    if request.method == 'POST':

        if not request.has_permission('edit', context):
            raise HTTPForbidden()

        if form.validate():
            upload_dir = request.registry.settings['studies.blob.dir']
            apply_data(Session, context, form.data, upload_dir)
            Session.flush()
            request.session.flash(
                _(u'Changes saved for: ${form}', mapping={
                    'form': context.schema.title}),
                'success')
            return HTTPFound(location=request.current_route_path(
                _route_name='studies.visit'))

    return {
        'visit': view_json(visit, request),
        'form': render_form(
            form,
            disabled=not request.has_permission('edit'),
            cancel_url=request.current_route_path(_route_name='studies.visit'),
            attr={
                'method': 'POST',
                'action': request.current_route_path(),
                'role': 'form'
            }
        ),
    }


def VisitSchema(context, request):

    def unique_cycle(form, field):
        is_new = isinstance(context, models.VisitFactory)
        patient = context.__parent__ if is_new else context.patient
        query = (
            Session.query(models.Visit)
            .filter(models.Visit.patient == patient)
            .filter(models.Visit.cycles.any(
                (~models.Cycle.is_interim)
                & (models.Cycle.id == field.data.id))))
        if not is_new:
            query = query.filter(models.Visit.id != context.id)
        other = query.first()
        if other:
            raise wtforms.ValidationError(request.localizer.translate(
                _(u'"${cycle}" already in use by visit on ${visit}'),
                mapping={
                    'cycle': field.data.title,
                    'visit': other.visit_date}))

    def unique_visit_date(form, field):
        is_new = isinstance(context, models.VisitFactory)
        patient = context.__parent__ if is_new else context.patient
        exists_query = (
            Session.query(models.Visit)
            .filter_by(patient=patient)
            .filter_by(visit_date=field.data))
        if not is_new:
            exists_query = exists_query.filter(models.Visit.id != context.id)
        (exists,) = Session.query(exists_query.exists()).one()
        if exists:
            raise wtforms.ValidationError(request.localizer.translate(
                _(u'Visit already exists')))

    class VisitForm(Form):
        cycles = wtforms.FieldList(
            ModelField(
                session=Session,
                class_=models.Cycle,
                validators=[
                    wtforms.validators.InputRequired(),
                    unique_cycle]),
            min_entries=1)
        visit_date = DateField(
            validators=[
                wtforms.validators.InputRequired(),
                unique_visit_date])
        include_forms = wtforms.BooleanField()
        include_specimen = wtforms.BooleanField()

    return VisitForm
