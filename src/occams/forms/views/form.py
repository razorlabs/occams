from pyramid.view import view_config
from sqlalchemy import orm, sql, null
from wtforms import Form, StringField, validators, ValidationError

from .. import _, log, Session, models
from ..form import CSRF


def is_unique_name(form, field):
    name_exists = sql.exists().where(models.Schema.name == field.data.lower())
    if not Session.query(name_exists).one():
        raise ValidationError(_(u'Form name already in use'))


class SchemaForm(Form):

    class Meta(object):
        csrf = True
        csrf_class = CSRF

    name = StringField(
        label=_('Schema Name'),
        description=_(
            u'The form\'s system name. '
            u'The name must not start with numbers or contain special '
            u'characters or spaces.'
            u'This name cannot be changed once the form is published.'),
        validators=[
            validators.required(),
            validators.Length(min=3, max=32),
            validators.Regexp(r'[a-zA-Z_][a-zA-Z0-9_]+'),
            is_unique_name])

    title = StringField(
        label=_(u'Form Title'),
        description=_(
            u'The human-readable name users will see when entering data.'),
        validators=[
            validators.required(),
            validators.Length(3, 128)])


@view_config(
    route_name='form_list',
    renderer='../templates/form/list.pt',
    permission='form_view')
def list_(request):
    return {}


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

    def jsonify(row):
        values = row._asdict()
        versions = (
            Session.query(models.Schema)
            .filter(models.Schema.name == row.name)
            .order_by(models.Schema.publish_date == null(),
                      models.Schema.publish_date.desc()))
        values['versions'] = [{
            'url': request.route_path(
                'version_view',
                form=row.name,
                version=version.publish_date or version.id),
            'status': 'draft' if not version.publish_date else 'published',
            'publish_date': version.publish_date and str(version.publish_date),
            'retract_date': version.retract_date and str(version.retract_date)
        } for version in versions]
        return values

    return [jsonify(r) for r in query]


@view_config(
    route_name='form_add',
    xhr=True,
    request_method='POST',
    permission='form_add',
    renderer='json')
def add(request):
    """
    Allows a user to create a new type of form.
    """
    form = SchemaForm(request.POST, csrf_context=request.session)
    if request.method == 'POST' and form.validate():
        schema = models.Schema()
        form.populate_obj(schema)
        Session.add(schema)
        Session.flush()
        # Versions not necessary since this is a brand new form
        return {
            'type': 'content',
            'name': schema.name,
            'has_private': schema.has_private,
            'title': schema.title,
            'is_new': True,
            'versions': [{
                'url': request.route_path('version_view',
                                          form=schema.name,
                                          version=schema.id),
                'label': _(u'draft')
            }]
        }
    return {
        'type': 'form',
        'title': _(u'Create Form'),
        'action': request.route_path('form_add'),
        'method': 'POST',
        'fields': [{
            'label': f.label.text,
            'description': f.description,
            'required': f.flags.required,
            'input_type': f.widget.input_type,
            'input': f(class_='form-control'),
            'value': f.data,
            'errors': f.errors,
            'order': i
            } for i, f in enumerate(form)],
        'cancel': _(u'Cancel'),
        'submit': _(u'Create'),
    }
