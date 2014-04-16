import colander
import deform.widget
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid_deform import CSRFSchema
from pyramid.view import view_config
from sqlalchemy import func, orm, sql

from occams.studies import _, models, Session


def find_study(request):
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


class StudySchema(CSRFSchema):

    id = colander.SchemaNode(
        colander.Int(),
        widget=deform.widget.HiddenWidget(),
        missing=None)

    name = colander.SchemaNode(
        colander.String(),
        title=_(u'URL Name'),
        description=_(u'ID for user (e.g. /studies/my-study)'))

    title = colander.SchemaNode(
        colander.String(),
        title=_(u'Title'))

    description = colander.SchemaNode(
        colander.String(),
        title=_(u'Description'),
        widget=deform.widget.TextAreaWidget(),
        missing=None)

    code = colander.SchemaNode(
        colander.String(),
        title=_(u'Code'))

    short_title = colander.SchemaNode(
        colander.String(),
        title=_(u'Printable Title'))

    consent_date = colander.SchemaNode(
        colander.Date(),
        title=_(u'Consent Date'))

    def validator(self, node, struct):
        name = struct['name']
        name_query = Session.query(models.Study).filter_by(name=name)
        if struct['id'] is not None:
            name_query = name_query.filter(models.Study.id != struct['id'])
        count = name_query.count()
        if count > 0:
            raise colander.Invalid('"%s" already exists' % struct['title'])


class ScheduleSchema(CSRFSchema):

    id = colander.SchemaNode(
        colander.Int(),
        widget=deform.widget.HiddenWidget(),
        missing=None)

    study_id = colander.SchemaNode(
        colander.Int(),
        widget=deform.widget.HiddenWidget(),
        missing=None)

    title = colander.SchemaNode(
        colander.String(),
        title=_(u'Title'))

    week = colander.SchemaNode(
        colander.Int(),
        title=_(u'Week Number'),
        missing=None)

    def validator(self, node, struct):
        pass


@view_config(
    route_name='study_list',
    permission='study_view',
    renderer='occams.studies:templates/study/list.pt')
def list_(request):
    layout = request.layout_manager.layout
    layout.title = _(u'Studies')
    layout.set_menu('study_list_menu')
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
    study = find_study(request)
    layout = request.layout_manager.layout
    layout.title = study.title
    layout.set_menu('study_view_menu', study=study)
    layout.set_details('study_details', study=study)
    layout.set_nav('study_nav', study=study)
    return {'study': study}


@view_config(
    route_name='study_ecrfs',
    permission='study_view',
    renderer='occams.studies:templates/study/ecrfs.pt')
def ecrfs(request):
    study = find_study(request)
    layout = request.layout_manager.layout
    layout.title = study.title
    layout.set_menu('study_view_menu', study=study)
    layout.set_details('study_details', study=study)
    layout.set_nav('study_nav', study=study)
    return {'study': study}


@view_config(
    route_name='study_schedule',
    permission='study_view',
    renderer='occams.studies:templates/study/schedule.pt')
def schedule(request):
    study = find_study(request)
    layout = request.layout_manager.layout
    layout.title = study.title
    layout.set_menu('study_view_menu', study=study)
    layout.set_details('study_details', study=study)
    layout.set_nav('study_nav', study=study)
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
    study = find_study(request)

    layout = request.layout_manager.layout
    layout.title = study.title
    layout.set_menu('study_view_menu', study=study)
    layout.set_details('study_details', study=study)
    layout.set_nav('study_nav', study=study)

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
    renderer='occams.studies:templates/form.pt')
@view_config(
    route_name='study_add',
    permission='study_add',
    xhr=True,
    renderer='occams.studies:templates/form.pt',
    layout='ajax_layout')
def add(request):
    schema = StudySchema(title=_(u'Add Study'))
    form = deform.Form(
        schema=schema.bind(request=request),
        buttons=[
            deform.Button('cancel', _(u'Cancel'), css_class='btn'),
            deform.Button('submit', _(u'Add'), css_class='btn btn-primary')])

    if 'cancel' in request.POST:
        request.session.flash(_(u'Changes canceled'), 'info')
        return HTTPFound(location=request.route_path('study_list'))

    if 'submit' in request.POST:
        try:
            appstruct = form.validate(request.POST.items())
        except deform.ValidationFailure as e:
            return {'form': e.render()}
        study = models.apply(models.Study(), appstruct)
        Session.add(study)
        Session.flush()
        study_url = request.current_route_path(_route_name='study_view',
                                               study_name=study.name)
        request.session.flash(_(u'New study added!', 'success'))
        return HTTPFound(location=study_url)

    return {'form': form.render()}


def query_enabled_ecrfs(study):
    StudySchema = orm.aliased(models.Schema, name='StudySchema')
    CurrentSchema = orm.aliased(models.Schema, name='CurrentSchema')
    study_schemata_query = (
        Session.query(models.Schema)
        .filter(models.Schema.categories.contains(study.category))
        .subquery('study_schemata'))
    ecrfs_query = (
        Session.query(
            StudySchema.id,
            StudySchema.name,
            StudySchema.title)
        .add_column(
            (study_schemata_query.c.id is not None).label('is_enabled'))
        .outerjoin(study_schemata_query,
                   study_schemata_query.c.id == StudySchema.id)
        .filter(~StudySchema.is_inline)
        .filter(StudySchema.publish_date == (
            Session.query(CurrentSchema.publish_date)
            .filter(CurrentSchema.name == StudySchema.name)
            .filter(CurrentSchema.state == 'published')
            .order_by(CurrentSchema.publish_date.desc())
            .limit(1)
            .correlate(StudySchema)
            .as_scalar()))
        .order_by(StudySchema.title.asc()))
    return ecrfs_query
