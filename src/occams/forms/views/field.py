from pyramid.httpexceptions import HTTPForbidden, HTTPNotFound
from pyramid.view import view_config
from six import iterkeys
from sqlalchemy import orm
from wtforms import (
    Form,
    validators, ValidationError,
    StringField, TextAreaField, BooleanField, HiddenField, IntegerField,
    FieldList, FormField)

from occams.datastore.models.schema import RE_VALID_NAME, RESERVED_WORDS

from .. import _, models, Session
from ..form import CsrfForm
from ..utils import move_item
from .version import get_schema


def get_attribute(request):
    """
    Helper method to retrieve the attribute from a URL request
    """
    form_name = request.matchdict['form']
    version = request.matchdict['version']
    field_name = request.matchdict['field']
    query = (
        Session.query(models.Attribute)
        .filter(models.Attribute.name == field_name)
        .join(models.Schema)
        .filter(models.Schema.name == form_name))

    if version.isdigit():
        query = query.filter(models.Schema.id == version)
    else:
        query = query.filter(models.Schema.publish_date == version)

    try:
        return query.one()
    except orm.exc.NoResultFound:
        raise HTTPNotFound


@view_config(
    name='field_list',
    xhr=True,
    renderer='json')
def list(request):
    """
    Return a a listing of the fields in the form
    """
    schema = get_schema(request)
    schema_json = schema.json()
    return {
        'attributes': schema_json['attributes'],
        'sections': schema_json['sections']
    }


def is_unique_name(form, field):
    """
    Verifies that an attribute name is unique within a schema
    """

    query = (
        Session.query(models.Attribute)
        .filter(models.Attribute.name.ilike(field.data))
        .filter(models.Attribute.schema_id == form.schema_id.data))

    # If editing (admin only), avoid false positive
    if form.id.data:
        query = query.filter(models.Attribute.id != form.id.data)

    if Session.query(query.exists()).one():
        raise ValidationError(_(u'Variable name already exists in this form'))


class ChoiceForm(Form):

    name = StringField(
        label=_(u'Stored Value'),
        validators=[
            validators.required(),
            validators.Length(min=1, max=8),
            validators.Regexp('-?[0-9]+')])

    title = StringField(
        title=_(u'Displayed Label'),
        validators=[
            validators.required()])


class FieldForm(CsrfForm):

    id = HiddenField()

    schema_id = HiddenField(validators=[validators.required()])

    section_id = HiddenField(validators=[validators.optional()])

    type = HiddenField()

    name = StringField(
        title=_(u'Variable Name'),
        description=_(
            u'Internal variable name, this value cannot be changed once it is '
            u'created.'
            ),
        validators=[
            validators.required(),
            validators.Regexp(
                RE_VALID_NAME,
                message=_(u'Not a valid variable name')),
            validators.NoneOf(
                RESERVED_WORDS,
                message=_(u'Can\'t use reserved programming word')),
            is_unique_name])

    title = StringField(
        label=_(u'Label'),
        description=_(u'The prompt for the user.'),
        validators=[
            validators.required()])

    description = TextAreaField(
        label=_(u'Help Text'),
        description=_(u'A short description about the field\'s purpose.'),
        validators=[validators.optional()])

    is_required = BooleanField(
        label=_(u'Required?'),
        description=_(
            u'If selected, the user will be required to enter a value.'))

    is_private = BooleanField(
        label=_(u'Does this field contain private information?'))

    # choice
    is_collection = BooleanField(
        label=_(u'Multiple Choice?'),
        description=_(u'If selected, the user may enter more than one value.'))

    # int
    precision = IntegerField(
        label=_(u'Decimal precision'),
        validators=[validators.optional()])

    # int/str
    value_min = StringField(
        label=_(u'Minimum value'),
        validators=[validators.optional()])

    # int/str
    value_max = StringField(
        label=_(u'Maximum value'),
        validators=[validators.optional()])

    # str
    format_expr = StringField(
        label=_(u'A regular expression to validate the field'),
        validators=[validators.optional()])

    constraint_expr = StringField(
        label=_(u'Constraint expression.'),
        description=_(
            u'A Javascript expression that returns a validation error, '
            u'if one occurs.'),
        validators=[validators.optional()])

    skip_expr = StringField(
        label=_(u'Skip expression.'),
        description=_(
            u'A Javascript expression that returns true if the field should '
            u'be skipped or false otherwise'),
        validators=[validators.optional()])

    # choice
    collection_min = IntegerField(
        label=(u'Minimum number of selections'))

    # choice
    collection_max = IntegerField(
        label=(u'Maximum number of selections'))

    # choice
    choices = FieldList(FormField(ChoiceForm))

    order = HiddenField()


@view_config(
    name='field_view',
    xhr=True,
    renderer='json',
    permission='form_view')
def view(request):
    attribute = get_attribute(request)
    attr_json = attribute.to_json()
    # TODO: add html preview?
    return attr_json


@view_config(
    name='field_add',
    xhr=True,
    renderer='json',
    permission='form_edit')
def add(request):
    """
    Add form for fields.

    Optionally takes a request variable ``order`` to preset where the
    field will be added (otherwise at the end of the form)
    """

    schema = get_schema(request)
    section = None
    type_ = request.matchdict['type']

    if schema.publish_date and not request.has_permission('admin'):
        raise HTTPForbidden('Cannot delete a field in a published form')

    add_form = FieldForm(request.POST)

    if request.method == 'POST' and add_form.validate():

        schema[add_form.name.data] = attribute = models.Attribute(
            section=section,
            name=add_form.name.data,
            title=add_form.title.data,
            description=add_form.description.data,
            type=type_,
            is_collection=add_form.is_collection.data,
            is_required=add_form.is_required.data,
            is_private=add_form.is_private.data,
        )

        move_item(schema.attributes, attribute, add_form.order.data)

        if type_ == 'choice':
            for i, choice_form in enumerate(add_form.choices.data):
                attribute[choice_form.name.data] = models.Choice(
                    name=choice_form.name.data,
                    title=choice_form.title.data,
                    order=i)

        # TODO return something useful
        return {}

    # TODO return something useful
    return {}


@view_config(
    name='field_edit',
    xhr=True,
    renderer='json',
    permission='form_edit')
def edit(request):
    """
    Edit view for an attribute
    """

    attribute = get_attribute(request)

    if attribute.schema.publish_date and not request.has_permission('admin'):
        raise HTTPForbidden('Cannot delete a field in a published form')

    edit_form = FieldForm(request.POST, attribute)

    if request.method == 'POST' and edit_form.validate():
        attribute.name = edit_form.name.data
        attribute.title = edit_form.title.data
        attribute.description = edit_form.description.data
        attribute.is_required = edit_form.is_required.data
        attribute.is_private = edit_form.is_private.data
        attribute.constraint_expr = edit_form.constraint_expr.data
        attribute.skip_expr = edit_form.skip_expr.data

        new_codes = dict([(c.name, c.title) for c in edit_form.choices.data])

        for code in iterkeys(attribute.choices):
            if code not in new_codes:
                del attribute.choices[code]

        for i, choice_form in enumerate(edit_form.choices.data):
            if choice_form.name.data in attribute.choices:
                choice = attribute.choices[choice_form.name.data]
            else:
                choice = models.Choice(attribute=attribute)
                Session.add(choice)
            choice.name = choice_form.name.data
            choice.title = choice_form.title.data
            choice.order = i

        # TODO return something useful
        return {}

    # TODO return something useful
    return {}


@view_config(
    name='field_move',
    xhr=True,
    request_method='POST',
    renderer='json',
    permission='form_edit')
def move(request):
    """
    Moves the field to the target section and display order within the form
    """
    attribute = get_attribute(request)

    if attribute.schema.publish_date and not request.has_permission('admin'):
        raise HTTPForbidden('Cannot delete a field in a published form')

    # Target section
    section_name = request.POST.get('section') or None

    # Move to the (valid) target section, if applicable
    if section_name:
        if section_name not in attribute.schema.sections:
            raise HTTPNotFound
        attribute.section = attribute.schema.sections[section_name]

    move_item(attribute.schema.attributes, attribute, request.POST['order'])

    # TODO: return something useful
    return {}


@view_config(
    name='field_delete',
    xhr=True,
    request_method='POST',
    renderer='json',
    permission='form_edit')
def delete(request):
    """
    Deletes the field from the form
    """
    attribute = get_attribute(request)
    if attribute.schema.publish_date and not request.has_permission('admin'):
        raise HTTPForbidden('Cannot delete a field in a published form')
    Session.delete(attribute)
    # TODO: return something useful
    return {}
