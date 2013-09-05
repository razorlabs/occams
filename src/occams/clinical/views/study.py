import datetime

import colander
import deform.widget
from pyramid.httpexceptions import HTTPFound
from pyramid_deform import CSRFSchema
from pyramid_layout.layout import layout_config
from pyramid_layout.panel import panel_config
from pyramid.view import view_config
from sqlalchemy import func, orm, sql
import transaction

from occams.datastore import model as datastore

from .. import _, log, models, Session


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
        name = tokenize(struct['title'])
        name_query = Session.query(models.Study).filter_by(name=name)
        if value['id'] is not None:
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
    renderer='occams.clinical:templates/study/list.pt')
def list_(request):
    layout = request.layout_manager.layout
    layout.content_title = _(u'Studies')
    layout.config_toolbar('study_toolbar_list')
    studies_query = (
        Session.query(models.Study)
        .order_by(models.Study.title.asc()))
    return {
        'studies': studies_query,
        'studies_count': studies_query.count()}


@view_config(
    route_name='study_view',
    permission='study_view',
    renderer='occams.clinical:templates/study/view.pt')
def view(request):
    return {}


@view_config(
    route_name='study_add',
    permission='study_add',
    renderer='occams.clinical:templates/form.pt')
@view_config(
    route_name='study_add',
    permission='study_add',
    xhr=True,
    renderer='occams.clinical:templates/form.pt',
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
        FiaSession.add(study)
        FiaSession.flush()
        study_url = request.current_route_path(_route_name='study_view',
                                                    study_name=study.name)
        request.session.flash(_(u'New study added!', 'success'))
        return HTTPFound(location=study_url)

    return {'form': form.render()}

