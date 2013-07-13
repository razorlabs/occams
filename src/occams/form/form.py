"""
Toolset for rendering datastore forms.
"""

import datetime
from pkg_resources import resource_filename

import colander
import deform
import deform.widget

from occams.datastore import model as datastore


def choice_widget_factory(attribute):
    choices = [(choice.name, choice.title) for choice in attribute.choices]
    if len(choices) <= 5:
        if attribute.is_collection:
            return deform.widget.CheckboxChoiceWidget(values=choices)
        else:
            return deform.widget.RadioChoiceWidget(values=choices)
    return deform.widget.SelectWidget(
        css_class='select2',
        template='select',
        multiple=attribute.is_collection,
        values=choices)


widgets = {
    'text': lambda a: deform.widget.TextAreaWidget(rows=5),
    'date': lambda a: deform.widget.DateInputWidget(type_name='date', css_class='datepicker'),
    'choice': choice_widget_factory }


types = {
    'boolean': colander.Bool,
    'integer': colander.Int,
    'decimal': colander.Decimal,
    'choice': colander.String,
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


def schema2colander(schema):
    """
    Converta a DataStore schema to a colander form schema
    """
    node = colander.SchemaNode(
        colander.Mapping(),
        name=schema.name,
        title=schema.title,
        description=schema.description)
    for section in schema.sections:
        subnode = colander.SchemaNode(
            colander.Mapping(),
            name=section.name,
            title=section.title,
            description=section.description)
        node.add(subnode)
        for attribute in section.attributes.itervalues():
            if not attribute.is_collection:
                type_ = types[attribute.type]()
            else:
                type_ = colander.Set()
            field = colander.SchemaNode(
                type_,
                name=attribute.name,
                title=attribute.title,
                description=attribute.description,
                missing=(colander.required if attribute.is_required else None))
            subnode.add(field)
            if attribute.type in widgets:
                field.widget = widgets[attribute.type](attribute)
    return node


class Form(deform.Form):
    """
    """

    default_renderer = WEB_FORM_RENDERER

    def __init__(self, *args, **kw):
        if isinstance(kw['schema'], datastore.Schema):
            kw['schema'] = schema2colander(kw['schema'])
        super(Form, self).__init__(*args, **kw)

