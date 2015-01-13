import json

from pyramid.session import check_csrf_token
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPBadRequest
import sqlalchemy as sa
from sqlalchemy import orm
import wtforms

from .. import _, Session, models


@view_config(
    route_name='forms',
    permission='view',
    renderer='../templates/form/list.pt')
def list_(request):
    return {}


@view_config(
    route_name='forms',
    permission='view',
    xhr=True,
    renderer='json')
def list_json(context, request):
    """
    Lists all forms used by instance.
    """
    return get_list_data(request)


@view_config(
    route_name='forms',
    permission='add',
    request_method='POST',
    request_param='files',
    xhr=True,
    renderer='json')
def upload(context, request):
    """
    Allows the user to upload a JSON file form.
    """
    check_csrf_token(request)

    files = request.POST.getall('files')

    if len(files) < 1:
        raise HTTPBadRequest(json={
            'user_message': _(u'Nothing uploaded')})

    schemata = [models.Schema.from_json(json.load(u.file)) for u in files]
    Session.add_all(schemata)
    Session.flush()

    return get_list_data(request, names=[s.name for s in schemata])


@view_config(
    route_name='forms',
    permission='add',
    request_method='POST',
    xhr=True,
    renderer='json')
def add(context, request):
    """
    Allows a user to create a new type of form.
    """
    check_csrf_token(request)

    form = FormForm.from_json(request.json_body)

    if not form.validate():
        raise HTTPBadRequest(json=form.errors)

    schema = models.Schema(**form.data)
    Session.add(schema)
    Session.flush()

    return get_list_data(request, names=[schema.name])['forms'][0]


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
                InnerSchema.publish_date == sa.null(),
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
            .order_by(models.Schema.publish_date == sa.null(),
                      models.Schema.publish_date.desc()))
        values['versions'] = [{
            '__url__':  request.route_path(
                'version',
                form=row.name,
                version=version.publish_date or version.id),
            'id': version.id,
            'name': version.name,
            'title': version.title,
            'publish_date': version.publish_date and str(version.publish_date),
            'retract_date': version.retract_date and str(version.retract_date)
        } for version in versions]
        return values

    return {
        'forms': [jsonify(r) for r in query]
    }


def check_unique_name(form, field):
    (exists,) = (
        Session.query(
            Session.query(models.Schema)
            .filter_by(name=field.data.lower())
            .exists())
        .one())
    if exists:
        raise wtforms.ValiationError(_(u'Form name already in use'))


class FormForm(wtforms.Form):

    name = wtforms.StringField(
        validators=[
            wtforms.validators.InputRequired(),
            wtforms.validators.Length(min=3, max=32),
            wtforms.validators.Regexp('^[a-zA-Z_][a-zA-Z0-9_]+$'),
            check_unique_name])

    title = wtforms.StringField(
        validators=[
            wtforms.validators.InputRequired(),
            wtforms.validators.Length(min=3, max=128)])
