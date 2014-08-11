from pyramid.httpexceptions import (
    HTTPBadRequest, HTTPForbidden, HTTPFound, HTTPNotFound)
from pyramid.view import view_config
import wtforms.fields.html5
import wtforms.widgets.html5

from .. import _, models, Session


@view_config(
    route_name='cycles',
    permission='study_view',
    renderer='../templates/study/schedule.pt')
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


class ScheduleForm(wtforms.Form):

    title = wtforms.StringField(
        title=_(u'Title'),
        validators=[wtforms.validators.required()])

    week = wtforms.IntegerField(
        title=_(u'Week Number'),
        validators=[wtforms.validators.required()])
