from good import *  # NOQA
import six
from pyramid.httpexceptions import HTTPOk, HTTPBadRequest
from pyramid.view import view_config

from occams.datastore.models.schema import RE_VALID_NAME, RESERVED_WORDS

from .. import _, models, Session
from ..validators import invalid2dict, Bytes, String, Integer


types = [
    {'name': 'choice', 'title': _(u'Answer choices')},
    {'name': 'date', 'title': _(u'Date')},
    {'name': 'datetime', 'title': _(u'Date & Time')},
    {'name': 'blob', 'title': _(u'File Attachement')},
    {'name': 'number', 'title': _(u'Number')},
    {'name': 'section', 'title': _(u'Section')},
    {'name': 'string', 'title': _(u'Text')},
    {'name': 'text', 'title': _(u'Paragraph Text')}]

valid_types = set([t['name'] for t in types])


@view_config(
    route_name='fields',
    permission='view',
    xhr=True,
    renderer='json')
def list_json(context, request):
    schema = context.__parent__
    return {
        '__url__':  request.route_path(
            'fields',
            form=schema.name,
            version=str(schema.publish_date or schema.id)),
        'fields': [view_json(a, request) for a in schema.itertraverse()]
        }


@view_config(
    route_name='field',
    permission='view',
    request_method='GET',
    xhr=True,
    renderer='json')
def view_json(context, request):
    """
    Returns JSON for a single attribute
    """
    schema = context.schema
    data = context.to_json(False)
    data['id'] = context.id
    data['__url__'] = request.route_path(
        'field',
        form=schema.name,
        version=str(schema.publish_date or schema.id),
        field=context.name)
    if context.attributes:
        data['fields'] = \
            [view_json(a, request) for a in context.itertraverse()]
    if context.choices:
        data['choices'] = [c.to_json() for c in context.iterchoices()]
    return data


@view_config(
    route_name='field',
    permission='edit',
    request_method='PUT',
    request_param='move',
    xhr=True,
    renderer='json')
def move_json(context, request):
    """
    Moves the field to the target section and display order within the form
    """
    check_csrf_token(request)

    schema = context.schema

    def not_self(value):
        if value == context.name:
            raise Invalid(_(u'Cannot move value into itself'))
        return value

    def not_section(value):
        if context.type == 'section' and schema[value].type == 'section':
            raise Invalid(_(u'Nested sections are not supported'))
        return value

    validator = Schema({
        Optional('into'): Maybe(
            All(Bytes(), In(schema), not_self, not_section)),
        Optional('after'): Maybe(All(Bytes(), In(schema), not_self)),
        Extra: Remove
        })

    try:
        data = validator(request.json_body)
    except Invalid as e:
        raise HTTPBadRequest(json=invalid2dict(e))

    attributes = sorted(six.itervalues(schema.attributes),
                        key=lambda a: a.order)
    attributes.remove(attribute)

    into = data['into'] and schema.attributes[data['into']]
    after = data['after'] and schema.attributes[data['after']]

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

    return HTTPOk()


@view_config(
    route_name='fields',
    permission='add',
    request_method='POST',
    xhr=True,
    renderer='json')
@view_config(
    route_name='field',
    permission='edit',
    request_method='PUT',
    xhr=True,
    renderer='json')
def edit_json(context, request):
    """
    Add/Edit form for fields.
    """
    check_csrf_token(request)

    validate = FieldSchema(context, request)

    try:
        data = validate(request.json_body)
    except Invalid as e:
        raise HTTPBadRequest(json=invalid2dict(e))

    if isinstance(context, models.Attribute):
        attribute = context
    else:
        attribute = schema.attributes[data['name']] = models.Attribute()

    attribute.apply(data)

    if not isinstance(context, models.Attribute):
        move_field_json(attribute, request)

    return view_json(attribute, request)


@view_config(
    route_name='fields',
    permission='edit',
    xhr=True,
    request_param='validate',
    renderer='json')
@view_config(
    route_name='field',
    permission='edit',
    xhr=True,
    request_param='validate',
    renderer='json')
def validate_value_json(context, request):
    """
    Helper method to return a validation status

    Note that BadRequest is not returned because the requested data
    in this context is the status string (not the status of the operation)

    Returns an OK response containing the validation status.
    """
    gschema = FieldSchema(context, request)
    if not prop or prop not in gschema:
        return HTTPOk(json=_(u'Server Error: No field specified'))
    else:
        try:
            gschema[prop](request.GET.get(prop))
        except Invalid as e:
            return HTTPOk(json=invalid2dict(e))
    return HTTPOk()


@view_config(
    route_name='field',
    permission='edit',
    request_method='DELETE',
    xhr=True,
    renderer='json')
def delete_json(context, request):
    """
    Deletes the field from the form
    """
    check_csrf_token(request)
    Session.delete(context)
    return HTTPOk()


def FieldSchema(context, request):

    def not_reserved_word(value):
        if value in RESERVED_WORDS:
            raise Invalid(_(u'Can\'t use reserved programming word'))
        return value

    def unique_name(value):
        """
        Verifies that an attribute name is unique within a schema
        """
        query = (
            Session.query(models.Attribute)
            .filter_by(schema=context.__parent__, name=value))
        if isinstance(context, models.Attribute):
            query = query.filter(models.Attribute.id != context.id)
        (exists,) = Session.query(query.exists()).one()
        if exists:
            raise Invalid(_(u'Variable name already exists in this form'))

    return Schema({
        'name': All(
            Bytes(),
            Match(RE_VALID_NAME, message=_(u'Not a valid variable name')),
            not_rerserved_word,
            unique_name),
        'title': String(),
        Optional('description'): Maybe(String()),
        'type': In(valid_types),
        'is_required': Boolean(),
        'is_private': Boolean(),
        Optional('is_system'): Maybe(Boolean()),
        Optional('is_readonly'): Maybe(Boolean()),

        # choice
        Optional('is_collection'): Maybe(Boolean()),
        Optional('is_shuffled'): Maybe(Boolean()),

        # number
        Optional('decimal_places'): Maybe(Integer()),

        # number/string/multiple-choice
        Optional('value_min'): Maybe(Integer()),
        Optional('value_man'): Maybe(integer()),

        # string
        Optional('pattern'): Maybe(Bytes()),

        Optional('choices'): Maybe([{
            'name': All(Bytes(), Length(min=1, max=8), Match('^-?[0-9]+$')),
            'title': String(),
            Extra: Remove
            }])
        })
