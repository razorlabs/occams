from pyramid.httpexceptions import HTTPBadRequest, HTTPForbidden
from pyramid.view import view_config
from sqlalchemy import func, orm, sql
import wtforms.fields.html5
import wtforms.widgets.html5

from .. import _, models, Session


@view_config(
    route_name='home',
    permission='view',
    renderer='../templates/study/list.pt')
def home(request):
    studies_query = (
        Session.query(models.Study)
        .order_by(models.Study.title.asc()))

    modified_query = (
        Session.query(models.Patient)
        .order_by(models.Patient.modify_date.desc())
        .limit(10))

    viewed = sorted((request.session.get('viewed') or {}).values(),
                    key=lambda v: v['view_date'],
                    reverse=True)

    return {
        'studies': studies_query,
        'studies_count': studies_query.count(),

        'modified': modified_query,
        'modified_count': modified_query.count(),

        'viewed': viewed,
        'viewed_count': len(viewed),
    }


@view_config(
    route_name='study',
    permission='view',
    renderer='../templates/study/view.pt')
def view(context, request):
    return {
        'cycles_data': cycles(context, request)
        }


@view_config(
    route_name='study',
    permission='view',
    xhr=True,
    renderer='json')
def cycles(context, request):
    StudyForm = orm.aliased(models.Schema, name='StudyForm')
    CurrentSchema = orm.aliased(models.Schema, name='CurrentSchema')
    study_schemata_query = (
        Session.query(models.Schema)
        .filter(models.Schema.categories.contains(study.category))
        .subquery('study_schemata'))

    ecrfs_query = (
        Session.query(
            StudyForm.id,
            StudyForm.name,
            StudyForm.title)
        .add_column(
            (study_schemata_query.c.id is not None).label('is_enabled'))
        .outerjoin(study_schemata_query,
                   study_schemata_query.c.id == StudyForm.id)
        .filter(~StudyForm.is_inline)
        .filter(StudyForm.publish_date == (
            Session.query(CurrentSchema.publish_date)
            .filter(CurrentSchema.name == StudyForm.name)
            .filter(CurrentSchema.state == 'published')
            .order_by(CurrentSchema.publish_date.desc())
            .limit(1)
            .correlate(StudyForm)
            .as_scalar()))
        .order_by(StudyForm.title.asc()))


    return {}



@view_config(
    route_name='study_progress',
    permission='view',
    renderer='../templates/study/progress.pt')
def progress(context, request):

    states_query = Session.query(models.State)

    VisitCycle = orm.aliased(models.Cycle)

    cycles_query = (
        Session.query(models.Cycle)
        .filter_by(study=context)
        .add_column(
            Session.query(func.count(models.Visit.id))
            .join(VisitCycle, models.Visit.cycles)
            .filter(VisitCycle.id == models.Cycle.id)
            .correlate(models.Cycle)
            .label('visits_count')))

    for state in states_query:
        cycles_query = cycles_query.add_column(
            Session.query(func.count(models.Visit.id))
            .join(VisitCycle, models.Visit.cycles)
            .filter(models.Visit.entities.any(state=state))
            .filter(VisitCycle.id == models.Cycle.id)
            .correlate(models.Cycle)
            .label(state.name))

    cycles_query = cycles_query.order_by(models.Cycle.week.asc())
    cycles_count = context.cycles.count()

    return {
        'states': states_query,
        'cycles': cycles_query,
        'cycles_count': cycles_count,
        'has_cycles': cycles_count > 0}


@view_config(
    route_name='study',
    permission='add',
    request_method='POST',
    xhr=True,
    renderer='json')
def add(request):
    form = StudyForm(request.POST)

    if not form.validate():
        raise HTTPBadRequest

    study = models.Study()
    form.populate_obj(study)
    Session.add(study)

    request.session.flash(_(u'New study added!', 'success'))

    return {'__next__': request.current_route_path(_route_name='study',
                                                   study=study.name)}


def is_unique_name(form, field):
    name_query = sql.exists().where(models.Schema.name == field.data.name)
    if hasattr(form, 'id'):
        name_query = name_query.where(models.Study.id != form.data.id)
    if Session.query(name_query).one():
        raise wtforms.ValidationError(
            _(u'"%s" already exists' % form.title.data))


class StudyForm(wtforms.Form):

    name = wtforms.StringField(
        label=_(u'URL Name'),
        description=_(u'ID for user (e.g. /studies/my-study)'),
        validators=[
            wtforms.validators.required(),
            wtforms.validators.Length(min=3, max=32),
            is_unique_name
        ])

    title = wtforms.StringField(
        label=_(u'Title'),
        validators=[
            wtforms.validators.required(),
            wtforms.validators.Length(min=3, max=32),
        ])

    description = wtforms.TextAreaField(
        title=_(u'Description'))

    code = wtforms.StringField(
        label=_(u'Code'),
        validators=[wtforms.validators.required()])

    short_title = wtforms.StringField(
        label=_(u'Printable Title'),
        validators=[wtforms.validators.required()])

    consent_date = wtforms.fields.html5.DateField(
        label=_(u'Consent Date'),
        validators=[wtforms.validators.required()])


class ScheduleForm(wtforms.Form):

    title = wtforms.StringField(
        title=_(u'Title'),
        validators=[wtforms.validators.required()])

    week = wtforms.IntegerField(
        title=_(u'Week Number'),
        validators=[wtforms.validators.required()])
