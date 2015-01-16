from datetime import datetime

from pyramid.httpexceptions import HTTPBadRequest
from pyramid.session import check_csrf_token
from pyramid.view import view_config
import sqlalchemy as sa
from sqlalchemy import orm
import wtforms
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField
from wtforms.ext.dateutil.fields import DateField

from .. import _, models, Session
from ..utils import wtferrors


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
            '__url__': request.route_path('form',
                                          patient=visit.patient.id,
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
    AJAX handler for validating cycles field
    """
    form = VisitSchema(context, request)(request.GET)
    if not form.validate() and 'cycles' in form.errors:
        return form.errors['cycles'][0]
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
    visit.cycles = form.cycles.data
    visit.visit_date = form.visit_date.data

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
            .filter(models.Cycle.id.in_([c.id for c in form.cycles.dat])))

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


def VisitSchema(context, request):

    def unique_cycles(form, field):
        is_new = isinstance(context, models.VisitFactory)
        patient = context.__parent__ if is_new else context.patient
        taken_query = (
            Session.query(models.Visit)
            .distinct()
            .filter(models.Visit.patient == patient)
            .join(models.Visit.cycles)
            .filter(models.Cycle.is_interim == sa.sql.false())
            .filter(models.Cycle.id.in_([c.id for c in field.data])))
        if not is_new:
            taken_query = taken_query.filter(models.Visit.id != context.id)
        taken = taken_query.all()
        if taken:
            raise wtforms.ValidationError(request.localizer.translate(
                _(u'Some selected cycles are already in use')))

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

    def available_cycles():
        return Session.query(models.Cycle).order_by('title')

    class VisitForm(wtforms.Form):
        cycles = QuerySelectMultipleField(
            query_factory=available_cycles,
            get_label='title',
            validators=[
                wtforms.validators.InputRequired(),
                wtforms.validators.Length(min=1),
                unique_cycles])
        visit_date = DateField(
            validators=[
                wtforms.validators.InputRequired(),
                unique_visit_date])
        include_forms = wtforms.BooleanField()
        include_specimen = wtforms.BooleanField()

    return VisitForm
