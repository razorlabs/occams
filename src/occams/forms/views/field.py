import json
from pyramid.httpexceptions import (
    HTTPOk, HTTPNotFound, HTTPForbidden, HTTPBadRequest)
from pyramid.view import view_config
import six
from sqlalchemy import orm
from webob.multidict import MultiDict
import wtforms

from occams.datastore.models.schema import RE_VALID_NAME, RESERVED_WORDS

from .. import _, models, Session
from .version import get_schema


types = [
    {'name': 'choice', 'title': _(u'Answer choices')},
    {'name': 'date', 'title': _(u'Date')},
    {'name': 'datetime', 'title': _(u'Date & Time')},
    {'name': 'blob', 'title': _(u'File Attachement')},
    {'name': 'number', 'title': _(u'Number')},
    {'name': 'section', 'title': _(u'Section')},
    {'name': 'string', 'title': _(u'Text')},
    {'name': 'text', 'title': _(u'Paragraph Text')}]


@view_config(
    route_name='field_list',
    xhr=True,
    request_method='GET',
    renderer='json',
    permission='form_view')
@view_config(
    route_name='field_list',
    request_param='alt=json',
    request_method='GET',
    renderer='json',
    permission='form_view')
def list_json(request):
    schema = get_schema(**request.matchdict)
    return get_fields_data(request, schema)


@view_config(
    route_name='field_view',
    xhr=True,
    request_method='GET',
    renderer='json',
    permission='form_view')
def view_json(request):
    """
    Returns JSON for a single attribute
    """
    attribute = get_attribute(**request.matchdict)
    return get_field_data(request, attribute)


@view_config(
    route_name='field_view',
    xhr=True,
    check_csrf=True,
    request_method='PUT',
    request_param='move',
    renderer='json',
    permission='form_edit')
def move_json(request):
    """
    Moves the field to the target section and display order within the form
    """
    attribute = get_attribute(**request.matchdict)
    schema = attribute.schema

    if schema.publish_date and not request.has_permission('form_amend'):
        raise HTTPForbidden(json={
            'user_message': _(u'Cannot delete a field in a published form'),
            'debug_message': _(u'Non-admin tried to edit a published form')
        })

    move_field(attribute.schema, attribute,
               into=extract_field(schema, request.json_body, 'parent'),
               after=extract_field(schema, request.json_body, 'after'))

    return HTTPOk()


@view_config(
    route_name='field_list',
    xhr=True,
    check_csrf=True,
    request_method='POST',
    renderer='json',
    permission='form_edit')
def add_json(request):
    """
    Add form for fields.
    """

    schema = get_schema(**request.matchdict)

    if schema.publish_date and not request.has_permission('form_amend'):
        raise HTTPForbidden(json={
            'user_message': _(u'Cannot add a field to a published form'),
            'debug_message': _(u'Non-admin tried to edit a published form')
        })

    add_form = FieldForm(data=request.json_body,
                         meta={'schema': schema})

    if not add_form.validate():
        raise HTTPBadRequest(json={
            'validation_errors': add_form.errors
        })

    attribute = models.Attribute()
    attribute.apply(add_form.data)
    schema.attributes[attribute.name] = attribute
    raise Exception
    move_field(attribute.schema, attribute,
               into=extract_field(schema, request.json_body, 'parent'),
               after=extract_field(schema, request.json_body, 'after'))

    return get_field_data(request, attribute)


@view_config(
    route_name='field_view',
    xhr=True,
    check_csrf=True,
    request_method='PUT',
    renderer='json',
    permission='form_edit')
def edit_json(request):
    """
    Edit view for an attribute
    """
    attribute = get_attribute(**request.matchdict)
    schema = attribute.schema

    if schema.publish_date and not request.has_permission('form_amend'):
        raise HTTPForbidden(json={
            'user_message': 'Cannot delete a field in a published form',
        })

    edit_form = FieldForm(
        data=request.json_body,
        meta={'schema': schema, 'attribute': attribute})

    if not edit_form.validate():
        raise HTTPBadRequest(json={
            'validation_errors': edit_form.errors
        })

    attribute.apply(edit_form.data)

    return get_field_data(request, attribute)


@view_config(
    route_name='field_list',
    xhr=True,
    check_csrf=True,
    request_method='POST',
    request_param='validate',
    permission='view')
def validate_add_json(request):
    schema = get_schema(**request.matchdict)
    return validate_field(FieldForm(request.POST,
                                    meta={'schema': schema}),
                          request.params.get('validate'))


@view_config(
    route_name='field_view',
    xhr=True,
    check_csrf=True,
    request_method='POST',
    request_param='validate',
    permission='view')
def validate_edit_json(request):
    attribute = get_attribute(**request.matchdict)
    return validate_field(FieldForm(request.POST,
                                    meta={'schema': attribute.schema,
                                          'attribute': attribute}),
                          request.params.get('validate'))


def validate_field(form, prop):
    """
    Helper method to return a validation status

    Note that BadRequest is not returned because the requested data
    in this context is the status string (not the status of the operation)

    Parameters:
    form -- the WTForm instance
    prop -- the properety in the form to validate

    Returns an OK response containing the validation status.
    """
    if not prop or prop not in form:
        return HTTPOk(json=_(u'Server Error: No field specified'))
    elif not form[prop].validate(form):
        return HTTPOk(json=form[prop].errors[0])
    return HTTPOk()


@view_config(
    route_name='field_view',
    xhr=True,
    check_csrf=True,
    request_method='DELETE',
    renderer='json',
    permission='form_edit')
def delete_json(request):
    """
    Deletes the field from the form
    """
    attribute = get_attribute(**request.matchdict)
    schema = attribute.schema
    if schema.publish_date and not request.has_permission('form_amend'):
        raise HTTPForbidden(json={
            'user_message': 'Cannot delete a field in a published form',
        })
    Session.delete(attribute)
    return HTTPOk()


def get_attribute(form=None, field=None, version=None, **kw):
    """
    Helper method to retrieve the attribute from a URL request
    """
    query = (
        Session.query(models.Attribute)
        .filter(models.Attribute.name == field)
        .join(models.Schema)
        .filter(models.Schema.name == form))
    try:
        if str(version).isdigit():
            return query.filter(models.Schema.id == version).one()
        else:
            return query.filter(models.Schema.publish_date == version).one()
    except orm.exc.NoResultFound:
        raise HTTPNotFound


def get_fields_data(request, schema):
    """
    Helper method to return fields JSON data
    """

    def fields(attributes):
        attributes = sorted(attributes, key=lambda i: i.order)
        return [get_field_data(request, a) for a in attributes]

    return {
        '__src__':  request.route_path(
            'field_list',
            form=schema.name,
            version=str(schema.publish_date or schema.id)),
        'fields': fields(a
                         for a in six.itervalues(schema.attributes)
                         if a.parent_attribute is None)
    }


def get_field_data(request, attribute):
    """
    Helper method to return field JSON data
    """
    schema = attribute.schema
    data = attribute.to_json(True)
    data['id'] = attribute.id
    data['__src__'] = request.route_path(
        'field_view',
        form=attribute.schema.name,
        version=str(schema.publish_date or schema.id),
        field=attribute.name)
    children = data.pop('attributes', None)
    if children:
        children = sorted(six.itervalues(children), key=lambda i: i['order'])
        data['fields'] = \
            [get_field_data(request, schema.attributes[f['name']])
             for f in children]
    choices = data.pop('choices', None)
    if choices:
        choices = sorted(six.itervalues(choices), key=lambda i: i['order'])
        data['choices'] = choices
    return data


def extract_field(schema, data, key):
    """
    Helper method to extract an attribute from request data
    """
    name = (data.get(key) or '').strip()
    if not name:
        return None
    if name not in schema.attributes:
        raise HTTPBadRequest(json={
            'user_message': _(
                u'Inavalid desitation field: ${name}',
                mapping={name: name}),
            'debug_message': _(
                u'Parent name specified is not in the form: ${name}',
                mapping={name: name}),
        })
    return schema.attributes[name]


def move_field(schema, attribute, into=None, after=None):
    """
    Moves the attribute to a new location in the form

    Parameters:
    schema -- Attribute's schema (in case we're dealing with a new field)
    attribute -- Source attribute
    into -- (optional) Desination parent, None implies root of form
    after -- (optional) Place after target, None implies first
    """
    assert schema is not None
    assert attribute is not None
    assert attribute != into
    assert attribute != after
    assert schema == attribute.schema
    assert into is None or schema == into.schema
    assert after is None or schema == after.schema

    # Move to a (valid) target section, if applicable
    if attribute.type == 'section' and into and into.type == 'section':
        raise HTTPBadRequest(json={
            'user_message': _(u'Moving to invalid section')
        })

    attributes = sorted(six.itervalues(schema.attributes),
                        key=lambda a: a.order)
    attributes.remove(attribute)

    if after is None:
        index = 0 if into is None else attributes.index(into) + 1
    elif after.type == 'section':
        index = attributes.index(after) + len(after.attributes)
    else:
        index = attributes.index(after) + 1

    attribute.parent_attribute = into
    attributes.insert(index, attribute)

    for i, a in enumerate(attributes):
        a.order = i


class ChoiceForm(wtforms.Form):

    name = wtforms.StringField(
        validators=[
            wtforms.validators.required(),
            wtforms.validators.Length(min=1, max=8),
            wtforms.validators.Regexp('-?[0-9]+')])

    title = wtforms.StringField(
        validators=[wtforms.validators.required()])


def validate_attribute_name(form, field):
    """
    Verifies that an attribute name is unique within a schema
    """
    schema = getattr(form.meta, 'schema')
    attribute = getattr(form.meta, 'attribute', None)
    names = set(schema.attributes.keys())

    # In edit-mode (admin only), avoid false positive
    if attribute:
        names.discard(attribute.name)

    if field.data in names:
        raise wtforms.ValidationError(
            _(u'Variable name already exists in this form'))


class FieldForm(wtforms.Form):

    name = wtforms.StringField(
        validators=[
            wtforms.validators.required(),
            wtforms.validators.Length(3, 20),
            wtforms.validators.Regexp(
                RE_VALID_NAME,
                message=_(u'Not a valid variable name')),
            wtforms.validators.NoneOf(
                RESERVED_WORDS,
                message=_(u'Can\'t use reserved programming word')),
            validate_attribute_name])

    title = wtforms.StringField(
        validators=[
            wtforms.validators.required()])

    description = wtforms.TextAreaField(
        validators=[wtforms.validators.optional()])

    type = wtforms.SelectField(
        choices=sorted((t['name'], t['title']) for t in types))

    is_required = wtforms.BooleanField()
    is_private = wtforms.BooleanField()
    is_system = wtforms.BooleanField()
    is_readonly = wtforms.BooleanField()
    is_collection = wtforms.BooleanField()  # choice only
    is_shuffled = wtforms.BooleanField()  # choice only

    # number
    decimal_places = wtforms.IntegerField(
        validators=[wtforms.validators.optional()])

    # number/string/multiple-choice
    value_min = wtforms.IntegerField()
    value_max = wtforms.IntegerField()

    # string
    pattern = wtforms.StringField(
        validators=[wtforms.validators.optional()])

    # choice
    choices = wtforms.FieldList(wtforms.FormField(ChoiceForm))
