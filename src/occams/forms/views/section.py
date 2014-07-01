import uuid

from pyramid.httpexceptions import HTTPForbidden, HTTPNotFound
from pyramid.view import view_config
from sqlalchemy import orm
from wtforms import validators, StringField, TextAreaField, HiddenField

from .. import _, models, Session
from ..form import CsrfForm
from ..utils import move_item
from .version import get_schema


def get_section(request):
    """
    Helper method to retrieve the attribute from a URL request
    """
    form_name = request.matchdict['form']
    version = request.matchdict['version']
    section_name = request.matchdict['section']
    query = (
        Session.query(models.Section)
        .filter(models.Section.name == section_name)
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


class SectionForm(CsrfForm):

    title = StringField(
        label=_(u'Label'),
        description=_(u'The prompt for the user.'),
        validators=[
            validators.required()])

    description = TextAreaField(
        label=_(u'Help Text'),
        description=_(u'A short description about the field\'s purpose.'),
        validators=[validators.optional()])

    order = HiddenField()


@view_config(
    name='section_view',
    xhr=True,
    renderer='json',
    permission='form_view')
def view(request):
    section = get_section(request)
    section_json = section.to_json()
    # TODO: add html preview?
    return section_json


@view_config(
    name='section_add',
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

    if schema.publish_date and not request.has_permission('admin'):
        raise HTTPForbidden('Cannot delete a field in a published form')

    add_form = SectionForm(request.POST)

    if request.method == 'POST' and add_form.validate():
        section = models.Section(name=str(uuid.uuid4()))
        add_form.populate_obj(section)
        schema[add_form.name.data] = section
        move_item(schema.sections, section, add_form.order.data)
        # TODO return something useful
        return {}

    # TODO return something useful
    return {}


@view_config(
    name='section_edit',
    xhr=True,
    renderer='json',
    permission='form_edit')
def edit(request):
    """
    Edit view for an attribute
    """

    section = get_section(request)

    if section.schema.publish_date and not request.has_permission('admin'):
        raise HTTPForbidden('Cannot delete a section in a published form')

    edit_form = SectionForm(request.POST, section)

    if request.method == 'POST' and edit_form.validate():
        section.title = edit_form.title.data
        section.description = edit_form.description.data

        # TODO return something useful
        return {}

    # TODO return something useful
    return {}


@view_config(
    name='section_move',
    xhr=True,
    request_method='POST',
    renderer='json',
    permission='form_edit')
def move(request):
    """
    Moves the field to the target section and display order within the form
    """
    section = get_section(request)

    if section.schema.publish_date and not request.has_permission('admin'):
        raise HTTPForbidden('Cannot delete a field in a published form')

    move_item(section.schema.sections, section, int(request.POST.get['order']))

    # TODO: return something useful
    return {}


@view_config(
    name='section_delete',
    xhr=True,
    request_method='POST',
    renderer='json',
    permission='form_edit')
def delete(request):
    """
    Deletes the field from the form
    """
    section = get_section(request)
    if section.schema.publish_date and not request.has_permission('admin'):
        raise HTTPForbidden('Cannot delete a field in a published form')
    Session.delete(section)
    # TODO: return something useful
    return {}
