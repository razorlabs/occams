from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import view_config
from sqlalchemy import func, orm, sql
from wtforms import (
    IntegerField,
    StringField,
    TextAreaField,
    ValidationError,
    validators,
    widgets
)
from wtforms.fields.html5 import DateField

from occams.studies import _, models, Session
from occams.studies.utils.form import CSRFForm


def get_study(request):
    """
    Uses the URL dispatch matching dictionary to find a study
    """
    try:
        return (
            Session.query(models.Study)
            .filter_by(name=request.matchdict['study_name'])
            .one())
    except orm.exc.NoResultFound:
        raise HTTPNotFound


def is_unique_name(form, field):
    name_query = sql.exists().where(models.Schema.name == field.data.name)
    if hasattr(form, 'id'):
        name_query = name_query.where(models.Study.id != form.data.id)
    if Session.query(name_query).one():
        raise ValidationError(_(u'"%s" already exists' % form.title.data))


class StudyForm(CSRFForm):

    id = IntegerField(widget=widgets.HiddenInput())

    name = StringField(
        label=_(u'URL Name'),
        description=_(u'ID for user (e.g. /studies/my-study)'),
        validators=[
            validators.required(),
            validators.Length(min=3, max=32),
            is_unique_name
        ])

    title = StringField(
        label=_(u'Title'),
        validators=[
            validators.required(),
            validators.Length(min=3, max=32),
        ])

    description = TextAreaField(
        title=_(u'Description'))

    code = StringField(
        label=_(u'Code'),
        validators=[validators.required()])

    short_title = StringField(
        label=_(u'Printable Title'),
        validators=[validators.required()])

    consent_date = DateField(
        label=_(u'Consent Date'),
        validators=[validators.required()])


class ScheduleForm(CSRFForm):

    id = IntegerField(widget=widgets.HiddenInput())

    title = StringField(
        title=_(u'Title'),
        validators=[validators.required()])

    week = IntegerField(
        title=_(u'Week Number'),
        validators=[validators.required()])

    def validator(self, node, struct):
        pass


@view_config(
    route_name='study_list',
    permission='study_view',
    renderer='occams.studies:templates/study/list.pt')
def list_(request):
    studies_query = (
        Session.query(models.Study)
        .order_by(models.Study.title.asc()))
    return {
        'studies': studies_query,
        'studies_count': studies_query.count()}


@view_config(
    route_name='study_view',
    permission='study_view',
    renderer='occams.studies:templates/study/view.pt')
def view(request):
    study = get_study(request)
    return {'study': study}


@view_config(
    route_name='study_ecrfs',
    permission='study_view',
    renderer='occams.studies:templates/study/ecrfs.pt')
def ecrfs(request):
    study = get_study(request)
    return {'study': study}


@view_config(
    route_name='study_schedule',
    permission='study_view',
    renderer='occams.studies:templates/study/schedule.pt')
def schedule(request):
    study = get_study(request)
    cycles_query = (
        Session.query(models.Cycle)
        .filter(models.Cycle.study == study)
        .order_by(models.Cycle.week.nullslast()))

    OuterSchema = orm.aliased(models.Schema, name='OuterSchema')

    ecrfs_query = (
        Session.query(OuterSchema.title)
        .add_columns(*[
            sql.exists([models.Schema.id])
            .where((models.Schema.name == OuterSchema.name)
                   & models.Schema.categories.contains(cycle.category))
            .label(cycle.name)
            for cycle in cycles_query])
        .filter(OuterSchema.categories.contains(study.category))
        .filter(OuterSchema.publish_date == (
            Session.query(models.Schema.publish_date)
            .filter(models.Schema.publish_date is not None)
            .filter(models.Schema.name == OuterSchema.name)
            .order_by(models.Schema.publish_date.desc())
            .limit(1)
            .correlate(OuterSchema)
            .as_scalar()))
        .order_by(OuterSchema.title.asc()))

    return {
        'study': study,
        'cycles': cycles_query,
        'has_cycles': cycles_query.count() > 0,
        'ecrfs': ecrfs_query}


@view_config(
    route_name='study_progress',
    permission='study_view',
    renderer='occams.studies:templates/study/progress.pt')
def progress(request):
    study = get_study(request)

    states_query = Session.query(models.State)

    VisitCycle = orm.aliased(models.Cycle)

    cycles_query = (
        Session.query(models.Cycle)
        .filter_by(study=study)
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
    cycles_count = study.cycles.count()

    return {
        'study': study,
        'states': states_query,
        'cycles': cycles_query,
        'cycles_count': cycles_count,
        'has_cycles': cycles_count > 0}


@view_config(
    route_name='study_add',
    permission='study_add',
    xhr=True,
    renderer='json')
def add(request):
    #title = _(u'Add Study')
    form = StudyForm(request.POST)

    if request.method == 'POST' and form.validate():
        study = models.Study()
        form.populate_obj(study)
        Session.add(study)
        study_url = request.current_route_path(_route_name='study_view',
                                               study_name=study.name)
        request.session.flash(_(u'New study added!', 'success'))
        return HTTPFound(location=study_url)

    return {'form': form}


def query_enabled_ecrfs(study):
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
    return ecrfs_query
