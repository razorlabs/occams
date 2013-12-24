"""
Toolset for rendering datastore forms.
"""

import datetime
from pkg_resources import resource_filename

import colander
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


def schema2colander(schema):
    """
    Converta a DataStore schema to a colander form schema
    """

    def nodify(item, type_=None):
        """ Helper method to create nodes from named records """
        return colander.SchemaNode(
            (type_ or colander.Mapping)(),
            name=item.name,
            title=item.title,
            description=item.description)

    node = nodify(schema)
    for section in schema.sections:
        subnode = nodify(section)
        node.add(subnode)
        for attribute in section.attributes.itervalues():
            if attribute.is_collection:
                type_ = colander.Set
            else:
                type_ = types[attribute.type]
            field = nodify(attribute, type_)
            if attribute.is_required:
                field.missing = colander.required
            if attribute.type in widgets:
                field.widget = widgets[attribute.type](attribute)
            subnode.add(field)

    return node
