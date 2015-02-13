from datetime import datetime

from pyramid.httpexceptions import \
    HTTPBadRequest, HTTPForbidden, HTTPFound, HTTPOk
from pyramid.session import check_csrf_token
from pyramid.view import view_config
import sqlalchemy as sa
from sqlalchemy import orm
import wtforms
from wtforms.ext.dateutil.fields import DateField

from occams.forms.renderers import \
    make_form, render_form, apply_data, entity_data

from .. import _, models, Session
from ..utils import wtferrors, ModelField


@view_config(
    route_name='visits',
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
    route_name='visit',
    permission='view',
    renderer='../templates/visit/view.pt')
def view(context, request):
    return {
        'visit': view_json(context, request)
        }


@view_config(
    route_name='visit',
    permission='view',
    xhr=True,
    renderer='json')
def view_json(context, request):
    visit = context
    entities_query = (
        Session.query(models.Entity)
        .options(orm.joinedload('schema'), orm.joinedload('state'))
        .join(models.Context)
        .filter_by(external='visit', key=visit.id))

    return {
        '__url__': request.route_path('visit',
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
            '__url__': request.route_path('patient',
                                          patient=visit.patient.pid),
            'site': {
                'title': visit.patient.site.title,
                },
            'pid': visit.patient.pid
            },
        'visit_date': visit.visit_date.isoformat(),
        'entities': [{
            '__url__': request.route_path('visit_form',
                                          patient=visit.patient.pid,
                                          visit=visit.visit_date.isoformat(),
                                          form=entity.id),
            'id': entity.id,
            'schema': {
                'name': entity.schema.name,
                'title': entity.schema.title,
                },
            'collect_date': entity.collect_date.isoformat(),
            'not_done': entity.not_done,
            'state': {
                'id': entity.state.id,
                'name': entity.state.name,
                'title': entity.state.title,
                }
            } for entity in entities_query]
        }


@view_config(
    route_name='visits_cycles',
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
    route_name='visits',
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
    route_name='visits',
    permission='add',
    request_method='POST',
    xhr=True,
    renderer='json')
@view_config(
    route_name='visit',
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
            visit.remove(cycle)
        else:
            incoming_cycles.remove(cycle)
    visit.cycles.extend(list(incoming_cycles))

    # TODO: hard coded for now, will be removed when workflows are in place
    default_state = (
        Session.query(models.State)
        .filter_by(name='pending-entry').one())

    if not is_new:
        for entity in visit.entities:
            if entity.state.name != default_state:
                entity.collect_date = form.visit_date.data

    if form.include_forms.data:
        CurrentSchema = orm.aliased(models.Schema)
        schemata_query = (
            Session.query(models.Schema)
            .select_from(models.Cycle)
            .join(models.Cycle.schemata)
            .filter(models.Schema.publish_date <= form.visit_date.data)
            .filter(models.Schema.publish_date == (
                Session.query(sa.func.max(CurrentSchema.publish_date))
                .filter(CurrentSchema.name == models.Schema.name)
                .correlate(models.Schema)
                .as_scalar()))
            .filter(models.Cycle.id.in_([c.id for c in form.cycles.data])))

        if isinstance(context, models.Visit):
            # Ignore already-added schemata
            schemata_query = schemata_query.filter(
                ~models.Schema.name.in_(
                    [entity.schema.name for entity in visit.entities]))

        for schema in schemata_query:
            visit.entities.add(models.Entity(
                schema=schema,
                collect_date=form.visit_date.data,
                state=default_state))

    Session.flush()

    return view_json(visit, request)


@view_config(
    route_name='visit',
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
    return {'__next__': request.route_path('patient',
                                           patient=context.patient.pid)}


@view_config(
    route_name='visit_form',
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
    route_name='visit_form',
    permission='view',
    renderer='../templates/visit/form.pt')
def form(context, request):

    visit = context.__parent__.__parent__
    allowed_schemata = (
        Session.query(models.Schema)
        .join(models.study_schema_table)
        .join(models.Study)
        .join(models.Cycle)
        .filter(models.Cycle.id.in_([cycle.id for cycle in visit.cycles])))
    allowed_versions = [s.publish_date for s in allowed_schemata]

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

    Form = make_form(Session, schema, allowed_versions=allowed_versions)
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

    form_id = 'visit-form'
    return {
        'visit': view_json(visit, request),
        'form_id': form_id,
        'form': render_form(form, attr={
            'id': form_id,
            'method': 'POST',
            'action': request.current_route_path(),
            'role': 'form'
        }),
    }


@view_config(
    route_name='visit_forms',
    xhr=True,
    permission='add',
    request_method='POST',
    renderer='json')
def form_add_json(context, request):
    check_csrf_token(request)

    def check_study_form(form, field):
        query = (
            Session.query(models.Visit)
            .filter(models.Visit.id == context.__parent__.id)
            .join(models.Visit.cycles)
            .join(models.Cycle.study)
            .filter(
                models.Cycle.schemata.any(id=field.data.id)
                | models.Study.schemata.any(id=field.data.id)))
        (exists,) = Session.query(query.exists()).one()
        if not exists:
            raise wtforms.ValidationError(request.localizer.translate(
                _('${schema} is not part of the studies for this visit'),
                mapping={'schema': field.data.title}))

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
        collect_date=context.__parent__.visit_date,
        state=default_state)
    context.__parent__.entities.add(entity)
    context.__parent__.patient.entities.add(entity)

    Session.flush()

    request.session.flash(
        _('Successfully added new ${form}',
            mapping={'form': entity.schema.title}),
        'success')

    return {
        '__next__': request.current_route_path(
            _route_name='visit_form', form=entity.id)
    }


@view_config(
    route_name='visit_forms',
    xhr=True,
    permission='delete',
    request_method='DELETE',
    renderer='json')
def form_delete_json(context, request):
    """
    Deletes forms in bulk
    """
    check_csrf_token(request)

    class DeleteForm(wtforms.Form):
        forms = wtforms.FieldList(ModelField(
            session=Session,
            class_=models.Entity))

    form = DeleteForm.from_json(request.json_body)

    if not form.validate():
        raise HTTPBadRequest(json={'errors': wtferrors(form)})

    entity_ids = [entity.id for entity in form.forms.data]

    (Session.query(models.Entity)
        .filter(models.Entity.id.in_(
            Session.query(models.Context.entity_id)
            .filter(models.Context.entity_id.in_(entity_ids))
            .filter(models.Context.external == u'visit')
            .filter(models.Context.key == context.__parent__.id)))
        .delete('fetch'))

    Session.flush()

    return HTTPOk()


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
        exists_query = (
            Session.query(models.Visit)
            .filter_by(visit_date=field.data))
        if isinstance(context, models.Visit):
            exists_query = exists_query.filter(models.Visit.id != context.id)
        (exists,) = Session.query(exists_query.exists()).one()
        if exists:
            raise wtforms.ValidationError(request.localizer.translate(
                _(u'Visit already exists')))

    class VisitForm(wtforms.Form):
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
