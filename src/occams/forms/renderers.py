import random

import six
import wtforms
import wtforms.widgets.html5


def render_field(field, **kw):
    """
    Renders a wtform field with HTML5 attributes applied
    TODO: consider pushing this to wtforms mainline...
    """
    if field.flags.required:
        kw['required'] = True
    # check validators Length, NumberRange or DateRange
    for validator in field.validators:
        if isinstance(validator, wtforms.validators.Length):
            # minlength is not supported by browsers
            if validator.min > -1:
                kw['data-minlength'] = validator.min
            # set maxlenght only, minlength is not supported by browsers
            if validator.max > -1:
                kw['maxlength'] = validator.max
        if isinstance(validator, wtforms.validators.NumberRange):
            if validator.min > -1:
                kw['min'] = validator.min
            if validator.max > -1:
                kw['max'] = validator.min
        if isinstance(validator, wtforms.validators.Regexp):
            kw['pattern'] = validator.regex.pattern
    return field(**kw)


def schema2wtf(schema):

    def make_field(attribute):
        kw = {
            'label': attribute.title,
            'description': attribute.description,
            'validators': []}

        if attribute.type == 'section':
            S = make_form(attribute.attributes)
            return wtforms.FormField(
                S, label=attribute.title, description=attribute.description)

        elif attribute.type == 'number':
            if attribute.decimal_places == 0:
                field_class = wtforms.IntegerField
                step = 1
            elif attribute.decimal_places is None:
                step = 'any'
                field_class = wtforms.DecimalField
            else:
                field_class = wtforms.DecimalField
                step = 1/float(pow(10, abs(attribute.decimal_places)))
            kw['widget'] = wtforms.widgets.html5.NumberInput(step)

        elif attribute.type == 'string':
            field_class = wtforms.StringField

        elif attribute.type == 'text':
            field_class = wtforms.TextAreaField

        elif attribute.type == 'date':
            field_class = wtforms.DateField

        elif attribute.type == 'datetime':
            field_class = wtforms.DateTimeField

        elif attribute.type == 'choice':
            choices = list(attribute.choices.values())
            if attribute.is_shuffled:
                choices = random.shuffle(choices)
            else:
                choices = sorted(choices, key=lambda c: c.order)
            kw['choices'] = [(c.name, c.title) for c in choices]
            if attribute.is_collection:
                field_class = wtforms.SelectMultipleField
                kw['widget'] = wtforms.widgets.ListWidget(prefix_label=False)
                kw['option_widget'] = wtforms.widgets.CheckboxInput()
            else:
                field_class = wtforms.SelectField
                kw['widget'] = wtforms.widgets.ListWidget(prefix_label=False)
                kw['option_widget'] = wtforms.widgets.RadioInput()

        elif attribute.type == 'blob':
            field_class = wtforms.FileField

        else:
            raise Exception(u'Unknown type: %s' % attribute.type)

        if attribute.is_required:
            kw['validators'].append(wtforms.validators.required())
        else:
            kw['validators'].append(wtforms.validators.optional())

        return field_class(**kw)

    def make_form(attributes):
        attributes = sorted(six.itervalues(attributes), key=lambda a: a.order)
        fields = dict([(a.name, make_field(a)) for a in attributes])
        return type('F', (wtforms.Form,), fields)

    return make_form(schema.attributes)
