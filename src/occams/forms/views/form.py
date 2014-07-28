import json

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPBadRequest
from sqlalchemy import func, orm, sql, null
import wtforms

from .. import _, Session, models


@view_config(
    route_name='form_list',
    renderer='../templates/form/list.pt',
    permission='form_view')
def list_(request):
    return {
        'add_form': SchemaForm(request.POST)
    }


@view_config(
    route_name='form_list',
    xhr=True,
    request_method='GET',
    renderer='json',
    permission='form_view')
def list_json(request):
    """
    Lists all forms used by instance.
    """
    return get_list_data(request)


@view_config(
    route_name='form_list',
    xhr=True,
    check_csrf=True,
    request_method='POST',
    request_param='files',
    permission='form_add',
    renderer='json')
def upload(request):
    """
    Allows the user to upload a JSON file form.
    """
    files = request.POST.getall('files')

    if len(files) < 1:
        raise HTTPBadRequest(json={
            'user_message': _(u'Nothing uploaded')})

    schemata = [models.Schema.from_json(json.load(u.file)) for u in files]
    Session.add_all(schemata)
    Session.flush()

    return get_list_data(request, names=[s.name for s in schemata])


@view_config(
    route_name='form_list',
    xhr=True,
    check_csrf=True,
    request_method='POST',
    permission='form_add',
    renderer='json')
def add(request):
    """
    Allows a user to create a new type of form.
    """
    form = SchemaForm(request.POST)

    if not form.validate():
        raise HTTPBadRequest(json={
            'validation_errors': form.errors,
            'data': form.data})

    schema = models.Schema()
    form.populate_obj(schema)
    Session.add(schema)
    Session.flush()

    # Versions not necessary since this is a brand new form
    return get_list_data(request, names=[schema.name])


def get_list_data(request, names=None):
    InnerSchema = orm.aliased(models.Schema)
    InnerAttribute = orm.aliased(models.Attribute)
    query = (
        Session.query(models.Schema.name)
        .add_column(
            Session.query(
                Session.query(InnerAttribute)
                .join(InnerSchema, InnerAttribute.schema)
                .filter(InnerSchema.name == models.Schema.name)
                .filter(InnerAttribute.is_private)
                .correlate(models.Schema)
                .exists())
            .as_scalar()
            .label('has_private'))
        .add_column(
            Session.query(InnerSchema.title)
            .filter(InnerSchema.name == models.Schema.name)
            .order_by(
                InnerSchema.publish_date == null(),
                InnerSchema.publish_date.desc())
            .limit(1)
            .correlate(models.Schema)
            .as_scalar()
            .label('title'))
        .group_by(models.Schema.name)
        .order_by(models.Schema.name))

    if names:
        query = query.filter(models.Schema.name.in_(names))

    def jsonify(row):
        values = row._asdict()
        versions = (
            Session.query(models.Schema)
            .filter(models.Schema.name == row.name)
            .order_by(models.Schema.publish_date == null(),
                      models.Schema.publish_date.desc()))
        values['versions'] = [{
            '__src__':  request.route_path(
                'version_view',
                form=row.name,
                version=version.publish_date or version.id),
            'publish_date': version.publish_date and str(version.publish_date),
            'retract_date': version.retract_date and str(version.retract_date)
        } for version in versions]
        return values

    return {
        'forms': [jsonify(r) for r in query]
    }


class SchemaForm(wtforms.Form):

    name = wtforms.StringField(
        label=_('System Name'),
        description=_(
            u'The form\'s system name. '
            u'The name must not start with numbers or contain special '
            u'characters or spaces.'
            u'This name cannot be changed once the form is published.'),
        validators=[
            wtforms.validators.required(),
            wtforms.validators.Length(min=3, max=32),
            wtforms.validators.Regexp(r'[a-zA-Z_][a-zA-Z0-9_]+',
                                      message=_(u'Invalid name format'))])

    title = wtforms.StringField(
        label=_(u'Form Title'),
        description=_(
            u'The human-readable name users will see when entering data.'),
        validators=[
            wtforms.validators.required(),
            wtforms.validators.Length(3, 128)])

    def validate_name(form, field):
        exists, = (
            Session.query(
                sql.exists()
                .where(func.lower(models.Schema.name) == field.data.lower()))
            .one())
        if exists:
            raise wtforms.ValidationError(_(u'Form name already in use'))
