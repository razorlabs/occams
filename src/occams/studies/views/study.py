from pyramid.httpexceptions import (
    HTTPBadRequest, HTTPForbidden, HTTPFound, HTTPNotFound)
from pyramid.view import view_config
from sqlalchemy import func, orm, sql
import wtforms.fields.html5
import wtforms.widgets.html5

from .. import _, models, Session


@view_config(
    route_name='home',
    permission='view',
    renderer='../templates/study/list.pt')
@view_config(
    route_name='studies',
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
    permission='study_view',
    renderer='../templates/study/view.pt')
def view(request):
    study = get_study(**request.matchdict)
    return {'study': study}


@view_config(
    route_name='study_ecrfs',
    permission='study_view',
    renderer='../templates/study/ecrfs.pt')
def ecrfs(request):
    study = get_study(**request.matchdict)
    return {'study': study}


@view_config(
    route_name='study_progress',
    permission='study_view',
    renderer='../templates/study/progress.pt')
def progress(request):
    study = get_study(**request.matchdict)

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
    route_name='study',
    permission='study_add',
    request_method='POST',
    xhr=True,
    renderer='json')
def add(request):
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


def get_study(study=None):
    """
    Uses the URL dispatch matching dictionary to find a study
    """
    try:
        return Session.query(models.Study).filter_by(name=study).one()
    except orm.exc.NoResultFound:
        raise HTTPNotFound


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
