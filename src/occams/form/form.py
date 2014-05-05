"""
Toolset for rendering datastore forms.
"""

import six
import wtforms
from wtforms.fields import html5


class MultiCheckboxField(wtforms.SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = wtforms.widgets.ListWidget(prefix_label=False)
    option_widget = wtforms.widgets.CheckboxInput()


def schema2wtf(schema):

    def make_field(attribute):
        kw = {
            'label': attribute.title,
            'description': attribute.description,
            'validators': []
        }

        if attribute.type == 'integer':
            field_class = html5.IntegerField
        elif attribute.type == 'decimal':
            field_class = wtforms.DecimalField
        elif attribute.type == 'string':
            field_class = wtforms.StringField
        elif attribute.type == 'text':
            field_class = wtforms.StringField
            kw['widget'] = wtforms.widgets.TextArea()
        elif attribute.type == 'date':
            field_class = wtforms.DateField
        elif attribute.type == 'datetime':
            field_class = wtforms.DateTimeField
        elif attribute.type == 'choice':
            kw['choices'] = [(c.name, c.title)
                             for c in sorted(six.itervalues(attribute.choices),
                                             key=lambda v: v.order)]
            if attribute.is_collection:
                field_class = MultiCheckboxField
            else:
                field_class = wtforms.RadioField
        elif attribute.type == 'blob':
            field_class = wtforms.FileField
        else:
            raise Exception(u'Unknown type: %s' % attribute.type)

        if attribute.is_required:
            kw['validators'].append(wtforms.validators.required())

        return field_class(**kw)

    F = type('F', (wtforms.Form,), {})

    # Non-fieldset fiels
    S = type('default', (wtforms.Form,), {})
    setattr(F, 'default', wtforms.FormField(S, label=u''))
    for attribute in sorted(six.itervalues(schema.attributes),
                            key=lambda v: v.order):
        if not attribute.section:
            setattr(S, attribute.name, make_field(attribute))

    # Fielset-fields
    for section in sorted(six.itervalues(schema.sections),
                          key=lambda v: v.order):
        S = type(str(section.name), (wtforms.Form,), {})
        setattr(F, section.name, wtforms.FormField(
            S,
            label=section.title,
            description=section.description,
        ))
        for attribute in sorted(six.itervalues(section.attributes),
                                key=lambda v: v.order):
            setattr(S, attribute.name, make_field(attribute))

    return F
