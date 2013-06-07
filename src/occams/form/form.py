"""
Toolset for rendering datastore forms.
"""

from pkg_resources import resource_filename

import datetime

import colander
import deform
import deform.widget

from zope.schema.interfaces import IChoice
from zope.schema.interfaces import IList
from zope.schema.interfaces import ITextLine
from zope.schema.interfaces import IText
import z3c.form.form
import z3c.form.group
import z3c.form.browser.textarea
from z3c.form.browser.radio import RadioFieldWidget
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.browser.textlines import TextLinesFieldWidget
from zope.schema.interfaces import IField

from occams.datastore import model as datastore

from .interfaces import TEXTAREA_SIZE


widgets = {
    'text': deform.widget.TextAreaWidget(),
    'date': deform.widget.DateInputWidget(type_name='date', css_class='datepicker') }


types = {
    'boolean': colander.Bool,
    'integer': colander.Int,
    'decimal': colander.Decimal,
    'string': colander.String,
    'text': colander.String,
    'date': colander.Date,
    'datetime': colander.DateTime}


# Define application-local renderers so we don't
# affect the entire python environment.

WEB_FORM_RENDERER = deform.ZPTRendererFactory([
    resource_filename('occams.form', 'templates/deform/overrides'),
    resource_filename('deform', 'templates')])


AJAX_FORM_RENDERER = deform.ZPTRendererFactory([
    resource_filename('occams.form', 'templates/deform/modal'),
    resource_filename('occams.form', 'templates/deform/overrides'),
    resource_filename('deform', 'templates')])



def custom_select_widget(multiple, values):
    if len(values) <= 5:
        if multiple:
            return deform.widget.CheckboxChoiceWidget(values = values)
        else:
            return deform.widget.RadioChoiceWidget(values = values)
    return deform.widget.SelectWidget(
            css_class='select2',
            template='select',
            multiple=multiple,
            values = values)


def schema2colander(schema):
    """
    Converta a DataStore schema to a colander form schema
    """

    node = colander.SchemaNode(
        colander.Mapping(),
        name=schema.name,
        title=schema.title,
        description=schema.description)

    for attribute in schema.itervalues():
        if attribute.type == 'object':
            subnode = schema2colander(attribute.object_schema)
            subnode.name = attribute.name
            subnode.title = attribute.title
            subnode.description = attribute.description
            node.add(subnode)
        else:
            if attribute.is_collection:
                attribute_type = colander.Sequence
                missing=[]
            else:
                attribute_type = types[attribute.type]
                missing=None
            field = colander.SchemaNode(
                attribute_type(),
                name=attribute.name,
                title=attribute.title,
                description=attribute.description,
                missing=(colander.required if attribute.is_required else missing),
                )
            if attribute.is_collection:
                subnode = colander.SchemaNode(types[attribute.type]())
                field.add(subnode)
            if attribute.type =='boolean':
                value_list = []
                value_list.extend([(at.value and 'true' or 'false', at.title) for at in attribute.choices])
                field.widget = custom_select_widget(attribute.is_collection, value_list)
            elif attribute.choices:
                value_list = []
                value_list.extend([(at.value, at.title) for at in attribute.choices])
                field.widget = custom_select_widget(attribute.is_collection, value_list)
            elif attribute.type in widgets:
                field.widget = widgets[attribute.type]
            node.add(field)
    return node


class Form(deform.Form):
    """
    """

    default_renderer = WEB_FORM_RENDERER

    def __init__(self, *args, **kw):
        if isinstance(kw['schema'], datastore.Schema):
            kw['schema'] = schema2colander(kw['schema'])
        super(Form, self).__init__(*args, **kw)

