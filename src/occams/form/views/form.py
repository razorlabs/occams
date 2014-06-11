from datetime import date

import colander
import deform
import deform.widget
from pyramid import httpexceptions as codes
from pyramid.view import view_config
from pyramid_deform import CSRFSchema
from sqlalchemy import func, orm, sql, null, cast, Unicode
import transaction

from occams.datastore.utils.sql import group_concat
from occams.datastore import models
from occams.form import _, Session, widgets


def is_unique_name(name):
    """
    Returns ``True`` if the name is not in use, ``False`` otherwise.
    """
    name_exists = sql.exists().where(models.Schema.name == name)
    return not Session.query(name_exists).scalar()


class CreateFormSchema(CSRFSchema):

    name = colander.SchemaNode(
        colander.String(),
        title=_('Schema Name'),
        description=_(
            u'The form\'s case-sensitive system name. '
            u'This name cannot be changed once the form is  published.'),
        validator=colander.All(
            colander.Length(3, 32),
            colander.Regex(r'[a-zA-Z_][a-zA-Z0-9_]+'),
            colander.Function(is_unique_name, _(u'Already exists'))))

    title = colander.SchemaNode(
        colander.String(),
        title=_(u'Form Title'),
        description=_(
            u'The human-readable name users will see when entering data.'),
        preparer=[
            lambda v: v.replace('\n', '') if v else v],
        validator=colander.Length(3, 32))

    description = colander.SchemaNode(
        colander.String(),
        title=_(u'Form Description'),
        missing=None,
        description=_(u'Brief information about the purpose of the form'),
        widget=deform.widget.TextAreaWidget())


@view_config(
    route_name='home',
    renderer='occams.form:templates/form/list.pt',
    permission='form_view')
def list_(request):
    """
    Lists all forms used by instance.
    """
    layout = request.layout_manager.layout
    layout.title = _(u'Forms')
    layout.set_menu('form_list_menu')
    query = (
        Session.query(models.Schema)
        .order_by(
            models.Schema.name,
            models.Schema.publish_date == null(),
            models.Schema.publish_date.desc()))
    return {
        'forms': iter(query),
        'forms_count': query.count(),
        'highlight': request.GET.get('highlight')}


@view_config(
    route_name='form_add',
    renderer='occams.form:templates/static/form.pt',
    xhr=True,
    permission='form_add',
    layout='ajax_layout')
def add(request):
    """
    Allows a user to create a new type of form.
    """
    form = deform.Form(
        action=request.current_route_path(),
        schema=CreateFormSchema(title=_(u'Create Form')).bind(request=request),
        buttons=[
            deform.Button(
                name='cancel',
                title=_('Cancel'),
                type='button',
                css_class='btn btn-link js-modal-dismiss'),
            deform.Button(
                name='submit',
                title=_('Create'),
                css_class='btn btn-primary')])
    form.widget = widgets.ModalFormWidget()
    if request.POST:
        try:
            data = form.validate(request.POST.items())
        except deform.ValidationFailure as e:
            request.response.status = '400 Bad Request'
            return {'form': e.render()}
        with transaction.manager:
            schema = models.Schema(name=data['name'], title=data['title'])
            Session.add(schema)
            return codes.HTTPCreated(
                # Can't send redirect because of same-origin-policy
                # But add the location so the client javascript can take action
                location=request.route_path('form_view',
                                            form_name=schema.name))
    return {'form': form.render()}


@view_config(
    route_name='form_view',
    renderer='occams.form:templates/form/view.pt',
    permission='form_view')
def view(request):
    """
    Displays information about the current publication of the form
    """
    name = request.matchdict['form_name']

    try:
        form = Session.query(models.Schema).filter_by(name=name).one()
    except orm.exc.NoResultFound:
        raise codes.HTTPNotFound

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


def query_form(name):
    """
    Returns a record for the current version of the specified form.
    """
    OuterSchema = orm.aliased(models.Schema, name='_outer_schema')
    query = (
        Session.query(OuterSchema.name)
        .add_column(
            Session.query(models.Schema.title)
            .filter(models.Schema.name == OuterSchema.name)
            .order_by(
                (models.Schema.publish_date != null()).desc(),
                models.Schema.publish_date.desc())
            .limit(1)
            .correlate(OuterSchema)
            .as_scalar()
            .label('title'))
        .filter(OuterSchema.name == name)
        .filter(OuterSchema.publish_date < date.today())
        .order_by(OuterSchema.publish_date.desc())
        .limit(1))
    return query


def query_categories(name):
    """
    Returns an iterable of the categories that are used
    for all versions of the specified form.
    """
    query = (
        Session.query(models.Category)
        .distinct()
        .filter(models.Category.schemata.any(name=name))
        .order_by(models.Category.title.asc()))
    return query


def query_versions(name):
    """
    Generates an iterable summary listing of forms in the system
    """
    OuterSchema = orm.aliased(models.Schema, name='_summary_schema')
    CreateUser = orm.aliased(models.User, name='_create_user')
    ModifyUser = orm.aliased(models.User, name='_modify_user')
    query = (
        Session.query(
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
            Session.query(func.count())
            .select_from(models.Schema)
            .outerjoin(models.Attribute,
                       models.Attribute.schema_id == models.Schema.id)
            .filter(models.Schema.id == OuterSchema.id)
            .correlate(OuterSchema)
            .as_scalar()
            .label('field_count'))
        .add_column((OuterSchema.publish_date == (
            Session.query(func.max(models.Schema.publish_date))
            .filter(models.Schema.publish_date < date.today())
            .filter(models.Schema.name == OuterSchema.name)
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
