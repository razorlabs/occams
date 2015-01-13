import six
from pyramid.httpexceptions import HTTPOk, HTTPBadRequest
from pyramid.session import check_csrf_token
from pyramid.view import view_config
import wtforms

from occams.datastore.models.schema import RE_VALID_NAME, RESERVED_WORDS

from .. import _, models, Session
from ._utils import jquery_wtform_validator

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

    def not_self(form, field):
        if field.data == context.name:
            raise wtforms.ValidationError(_(u'Cannot move value into itself'))

    def not_section(form, field):
        if context.type == 'section' and schema[field.data].type == 'section':
            raise wtforms.ValidationError(
                _(u'Nested sections are not supported'))

    class MoveForm(wtforms.Form):
        into = wtforms.StringField(
            validators=[
                wtforms.validators.AnyOf(
                    schema.attributes, message=_(u'Does not exist')),
                not_self,
                not_section])
        after = wtforms.StringField(
            validators=[
                wtforms.validators.AnyOf(
                    schema.attributes, message=_(u'Does not exist')),
                not_self])

    form = MoveForm.from_json(request.json_body)

    if not form.validate():
        raise HTTPBadRequest(json=form.errors)

    attributes = sorted(six.itervalues(schema.attributes),
                        key=lambda a: a.order)
    attributes.remove(context)

    into = form.into.data and schema.attributes[form.into.data]
    after = form.after.data and schema.attributes[form.after.data]

    if after is None:
        index = 0 if into is None else attributes.index(into) + 1
    elif after.type == 'section':
        index = attributes.index(after) + len(after.attributes)
    else:
        index = attributes.index(after) + 1

    context.parent_attribute = into
    attributes.insert(index, context)

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

    form = FieldFormFactory(context, request).from_json(request.json_body)

    if not form.validate():
        raise HTTPBadRequest(json=form.errors)

    if isinstance(context, models.Attribute):
        attribute = context
    else:
        # Add the attribute and temporarily set to large display order
        attribute = models.Attribute(schema=context.__parent__, order=-1)
        Session.add(attribute)

    attribute.apply(form.data)
    Session.flush()

    if not isinstance(context, models.Attribute):
        # now we can move the attribute
        move_json(attribute, request)

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
    FieldForm = FieldFormFactory(context, request)
    return jquery_wtform_validator(FieldForm, context, request)


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


def FieldFormFactory(context, request):

    def unique_variable(form, field):
        is_new = isinstance(context, models.AttributeFactory)
        schema = context.__parent__ if is_new else context.schema
        query = (
            Session.query(models.Attribute)
            .filter_by(name=field.data, schema=schema))
        if not is_new:
            query = query.filter(models.Attribute.id != context.id)
        (exists,) = Session.query(query.exists()).one()
        if exists:
            raise wtforms.ValidatonError(
                _(u'Variable name already exists in this form'))

    class ChoiceForm(wtforms.Form):
        name = wtforms.StringField(
            validators=[
                wtforms.validators.InputRequired(),
                wtforms.validators.Length(min=1, max=8),
                wtforms.validators.Regexp('^-?[0-9]+$')])
        title = wtforms.StringField(
            validators=[wtforms.validators.InputRequired()])

    class FieldForm(wtforms.Form):
        name = wtforms.StringField(
            validators=[
                wtforms.validators.InputRequired(),
                wtforms.validators.Length(min=2, max=20),
                wtforms.validators.Regexp(
                    RE_VALID_NAME,
                    message=_(u'Not a valid variable name')),
                wtforms.validators.NoneOf(
                    RESERVED_WORDS,
                    message=_(u'Can\'t use reserved programming word')),
                unique_variable])
        title = wtforms.StringField(validators=[
            wtforms.validators.InputRequired()])
        description = wtforms.StringField()
        type = wtforms.StringField(
            validators=[
                wtforms.validators.InputRequired(),
                wtforms.validators.AnyOf(set(t['name'] for t in types))])
        is_required = wtforms.BooleanField()
        is_private = wtforms.BooleanField()
        is_system = wtforms.BooleanField()
        is_readonly = wtforms.BooleanField()
        is_collection = wtforms.BooleanField()      # Choice
        is_shuffled = wtforms.BooleanField()        # Choice
        decimal_places = wtforms.IntegerField()     # Numbers
        value_min = wtforms.IntegerField()          # Number/String/Multichoice
        value_max = wtforms.IntegerField()          # Number/String/Multichoice
        pattern = wtforms.StringField()             # String
        choices = wtforms.FieldList(wtforms.FormField(ChoiceForm))

    return FieldForm
