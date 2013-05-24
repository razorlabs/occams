import datetime
import re

import colander
import deform
import deform.widget
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import view_config
from pyramid_deform import CSRFSchema
from pyramid_layout.panel import panel_config
from sqlalchemy import func, orm, sql

from occams.datastore import model as datastore

from .. import _, Session, Logger
from . import widgets


def is_unique_name(name):
    """ Returns ``True`` if the name is not in use, ``False`` otherwise.
    """
    name_exists = sql.exists().where(datastore.Schema.name == name)
    return not Session.query(name_exists).scalar()


class CreateFormSchema(colander.MappingSchema):

    name = colander.SchemaNode(
        colander.String(),
        title=_('Schema Name'),
        description=_(
            u'The form\'s system name. '
            u'In SQL parlance this is the \'table\' name. '
            u'Note that this value is case sensitive and is used in the URL, '
            u'so choosing a concise and convenient name is encouraged. '
            u'Also note that this value cannot be changed once the form is '
            u'published.'),
        validator=colander.All(
            colander.Length(3, 32),
            colander.Regex(r'[a-zA-Z_][a-zA-Z0-9_]+'),
            colander.Function(is_unique_name, _(u'Already exists'))))

    title = colander.SchemaNode(
        colander.String(),
        title=_(u'Form Title'),
        description=_(
            u'The human readable name that users will see when entering data.'),
        preparer=[
            lambda v: v.replace('\n', '') if v else v],
        validator=colander.Length(3, 32))

    copyfrom = colander.SchemaNode(
        colander.String(),
        title=_(u'Copy From'),
        description=_(
            u'Optionally, you can copy fields from another form into the '
            u'newly created form'),
        missing=colander.null)



@view_config(
    route_name='home',
    renderer='occams.form:/templates/form/list.pt',
    layout='web_layout')
def list_(request):
    """ Lists all forms used by instance.
    """
    layout = request.layout_manager.layout
    layout.content_title = _(u'Forms')
    layout.set_toolbar('form_list_toolbar')
    query = query_names(Session)
    return {
        'forms': iter(query),
        'forms_count': query.count()}


@view_config(
    route_name='form_add',
    renderer='occams.form:/templates/form/add.pt',
    xhr=True,
    layout='ajax_layout')
def add(request):
    """ Allows a user to create a new type of form.
    """
    layout = request.layout_manager.layout
    layout.content_title = _(u'Create New Form')
    form_renderer = widgets.WEB_FORM_RENDERER
    if request.is_xhr:
        # Use the ajax version instead of the default
        form_renderer = widgets.AJAX_FORM_RENDERER
    form = deform.Form(
        action=request.current_route_path(),
        schema=CreateFormSchema(title=_(u'Create Form')),
        renderer=form_renderer,
        buttons=[
            deform.Button('cancel', title=_('Cancel'), type='button', css_class='btn'),
            deform.Button('submit', title=_('Create'), css_class='btn btn-primary')])
    if 'submit' in request.POST:
        try:
            data = form.validate(request.POST.items())
        except deform.ValidationFailure as e:
            request.response.status = '400 Bad Request'
            return {'form': e}
        schema = datastore.Schema(name=data['name'], title=['title'])
        Session.add(schema)
        request.response.status = '201 Created'
        return {}
    return {'form': form}


@view_config(
    route_name='form_view',
    renderer='occams.form:/templates/form/view.pt',
    layout='web_layout')
def view(request):
    """ Displays information about the current publication of the form
    """
    return {}


@panel_config(
    name='form_list_toolbar',
    renderer='occams.form:/templates/form/panels/list_toolbar.pt')
def list_toolbar(context, request):
    return {}


def query_names(session):
    """ Generates an iterable summary of the form names in the system
    """
    SummarySchema = orm.aliased(datastore.Schema, name='_summary_schema')
    query = (
        session.query(SummarySchema.name)
        .distinct()
        .add_column(
            session.query(datastore.Schema.title)
            .filter(datastore.Schema.name == SummarySchema.name)
            .order_by(
                (datastore.Schema.publish_date != None).desc(),
                datastore.Schema.publish_date.desc())
            .limit(1)
            .correlate(SummarySchema)
            .as_scalar()
            .label('title'))
        .add_column(
            session.query(func.min(datastore.Schema.publish_date))
            .filter(datastore.Schema.name == SummarySchema.name)
            .correlate(SummarySchema)
            .as_scalar()
            .label('start_date'))
        .add_column(
            session.query(func.max(datastore.Schema.publish_date))
            .filter(datastore.Schema.name == SummarySchema.name)
            .correlate(SummarySchema)
            .as_scalar()
            .label('publish_date'))
        .add_column(
            session.query(func.count())
            .filter(datastore.Schema.name == SummarySchema.name)
            .filter(datastore.Schema.publish_date != None)
            .correlate(SummarySchema)
            .as_scalar()
            .label('version_count'))
        .filter(~SummarySchema.is_inline)
        .order_by(SummarySchema.title.asc()))
    return query


def query_summary(session):
    """ Generates an iterable summary listing of forms in the system
    """
    SummarySchema = orm.aliased(datastore.Schema, name='_summary_schema')
    CreateUser = orm.aliased(datastore.User, name='_create_user')
    ModifyUser = orm.aliased(datastore.User, name='_modify_user')
    SubSchema = orm.aliased(datastore.Schema, name='_sub_schema')
    SubAttribute = orm.aliased(datastore.Attribute, name='_sub_attribute')
    query = (
        session.query(
            SummarySchema.id.label('id'),
            SummarySchema.name.label('name'),
            SummarySchema.title.label('title'),
            SummarySchema.revision.label('revision'),
            SummarySchema.state.label('state'),
            SummarySchema.publish_date.label('publish_date'),
            SummarySchema.create_date.label('create_date'),
            CreateUser.key.label('create_user'),
            SummarySchema.modify_date.label('modify_date'),
            ModifyUser.key.label('modify_user'))
        .add_column(
            session.query(func.count())
            .select_from(datastore.Schema)
            .outerjoin(datastore.Attribute,
                datastore.Attribute.schema_id == datastore.Schema.id)
            .outerjoin(SubSchema,
                SubSchema.id == datastore.Attribute.object_schema_id)
            .outerjoin(SubAttribute, SubAttribute.schema_id == SubSchema.id)
            .filter(datastore.Schema.id == SummarySchema.id)
            .correlate(SummarySchema)
            .as_scalar()
            .label('field_count'))
        .add_column((SummarySchema.publish_date == (
            session.query(func.max(datastore.Schema.publish_date))
            .filter(datastore.Schema.state == 'published')
            .filter(datastore.Schema.publish_date < datastore.NOW)
            .filter(datastore.Schema.name == SummarySchema.name)
            .correlate(SummarySchema)
            .as_scalar())).label('is_current'))
        .join(CreateUser, SummarySchema.create_user_id == CreateUser.id)
        .join(ModifyUser, SummarySchema.modify_user_id == ModifyUser.id)
        .filter(~SummarySchema.is_inline)
        .order_by(
            SummarySchema.title.asc(),
            (SummarySchema.publish_date != None).desc(),
            SummarySchema.publish_date.desc()))
    return query

