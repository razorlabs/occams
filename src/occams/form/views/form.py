import datetime
import re

import colander
import deform
import deform.widget
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import view_config
from pyramid_deform import CSRFSchema
from pyramid_layout.panel import panel_config
from sqlalchemy import func, orm, sql, null

from occams.datastore import model as datastore

from occams.form import _, Session, log, widgets


def is_unique_name(name):
    """
    Returns ``True`` if the name is not in use, ``False`` otherwise.
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
            u'The human readable name users will see when entering data.'),
        preparer=[
            lambda v: v.replace('\n', '') if v else v],
        validator=colander.Length(3, 32))

    # TODO: this is still being worked out
    copyfrom = colander.SchemaNode(
        colander.String(),
        title=_(u'Copy From'),
        description=_(
            u'Optionally, you can copy fields from another form into the '
            u'newly created form'),
        missing=colander.null)


@view_config(
    route_name='home',
    renderer='occams.form:templates/form/list.pt',
    permission='form_view',
    layout='web_layout')
def list_(request):
    """
    Lists all forms used by instance.
    """
    layout = request.layout_manager.layout
    layout.content_title = _(u'Forms')
    layout.set_toolbar('form_list_toolbar')
    query = query_names(Session)
    return {
        'forms': iter(query),
        'forms_count': query.count(),
        'highlight': request.GET.get('highlight')}


@view_config(
    route_name='form_add',
    renderer='occams.form:templates/form/add.pt',
    xhr=True,
    permission='form_add',
    layout='ajax_layout')
def add(request):
    """
    Allows a user to create a new type of form.
    """
    form = deform.Form(
        action=request.current_route_path(),
        schema=CreateFormSchema(title=_(u'Create Form')),
        renderer=widgets.AJAX_FORM_RENDERER,
        buttons=[
            deform.Button(
                name='cancel',
                title=_('Cancel'),
                type='button',
                css_class='btn'),
            deform.Button(
                name='submit',
                title=_('Create'),
                css_class='btn btn-primary')])
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
    renderer='occams.form:templates/form/view.pt',
    permission='form_view',
    layout='web_layout')
def view(request):
    """
    Displays information about the current publication of the form
    """
    name = request.matchdict['form_name']

    try:
        form = query_form(Session, name).one()
    except orm.exc.NoResultFound:
        raise HTTPNotFound

    categories = query_categories(Session, name)
    versions = query_versions(Session, name)

    # Configure the layout and render the results
    layout = request.layout_manager.layout
    layout.content_title = form.title
    return {
        'form': form,
        'categories_count': categories.count(),
        'categories': iter(categories),
        'versions_count': versions.count(),
        'versions': iter(versions)}


@panel_config(
    name='form_list_toolbar',
    renderer='occams.form:templates/form/panels/list_toolbar.pt')
def list_toolbar(context, request):
    return {}


def query_form(session, name):
    """
    Returns a record for the current version of the specified form.
    """
    OuterSchema = orm.aliased(datastore.Schema, name='_outer_schema')
    query = (
        session.query(OuterSchema.name)
        .add_column(
            session.query(datastore.Schema.title)
            .filter(datastore.Schema.name == OuterSchema.name)
            .order_by(
                (datastore.Schema.publish_date != null()).desc(),
                datastore.Schema.publish_date.desc())
            .limit(1)
            .correlate(OuterSchema)
            .as_scalar()
            .label('title'))
        .filter(OuterSchema.name == name)
        .filter(OuterSchema.publish_date < datastore.NOW)
        .order_by(OuterSchema.publish_date.desc())
        .limit(1))
    return query


def query_categories(session, name):
    """
    Returns an iterable of the categories that are used
    for all versions of the specified form.
    """
    query = (
        Session.query(datastore.Category)
        .distinct()
        .filter(datastore.Category.schemata.any(name=name))
        .order_by(datastore.Category.title.asc()))
    return query


def query_names(session):
    """
    Generates an iterable summary of the form names in the system
    """
    OuterSchema = orm.aliased(datastore.Schema, name='_summary_schema')
    query = (
        session.query(OuterSchema.name)
        .distinct()
        .add_column(
            session.query(datastore.Schema.title)
            .filter(datastore.Schema.name == OuterSchema.name)
            .order_by(
                (datastore.Schema.publish_date != null()).desc(),
                datastore.Schema.publish_date.desc())
            .limit(1)
            .correlate(OuterSchema)
            .as_scalar()
            .label('title'))
        .add_column(
            session.query(func.min(datastore.Schema.publish_date))
            .filter(datastore.Schema.name == OuterSchema.name)
            .correlate(OuterSchema)
            .as_scalar()
            .label('start_date'))
        .add_column(
            session.query(func.max(datastore.Schema.publish_date))
            .filter(datastore.Schema.name == OuterSchema.name)
            .correlate(OuterSchema)
            .as_scalar()
            .label('publish_date'))
        .add_column(
            session.query(func.count())
            .filter(datastore.Schema.name == OuterSchema.name)
            .filter(datastore.Schema.publish_date != null())
            .correlate(OuterSchema)
            .as_scalar()
            .label('version_count'))
        .order_by(OuterSchema.title.asc()))
    return query


def query_versions(session, name):
    """
    Generates an iterable summary listing of forms in the system
    """
    OuterSchema = orm.aliased(datastore.Schema, name='_summary_schema')
    CreateUser = orm.aliased(datastore.User, name='_create_user')
    ModifyUser = orm.aliased(datastore.User, name='_modify_user')
    query = (
        session.query(
            OuterSchema.id.label('id'),
            OuterSchema.name.label('name'),
            OuterSchema.title.label('title'),
            OuterSchema.revision.label('revision'),
            OuterSchema.publish_date.label('publish_date'),
            OuterSchema.retract_date.label('retract_date'),
            OuterSchema.create_date.label('create_date'),
            CreateUser.key.label('create_user'),
            OuterSchema.modify_date.label('modify_date'),
            ModifyUser.key.label('modify_user'))
        .add_column(
            session.query(func.count())
            .select_from(datastore.Schema)
            .outerjoin(datastore.Attribute,
                       datastore.Attribute.schema_id == datastore.Schema.id)
            .filter(datastore.Schema.id == OuterSchema.id)
            .correlate(OuterSchema)
            .as_scalar()
            .label('field_count'))
        .add_column((OuterSchema.publish_date == (
            session.query(func.max(datastore.Schema.publish_date))
            .filter(datastore.Schema.publish_date < datastore.NOW)
            .filter(datastore.Schema.name == OuterSchema.name)
            .correlate(OuterSchema)
            .as_scalar())).label('is_current'))
        .join(CreateUser, OuterSchema.create_user_id == CreateUser.id)
        .join(ModifyUser, OuterSchema.modify_user_id == ModifyUser.id)
        .filter(OuterSchema.name == sql.bindparam('name'))
        .order_by(
            OuterSchema.title.asc(),
            (OuterSchema.publish_date != null()).asc(),
            OuterSchema.publish_date.desc()))
    return query.params(name=name)
