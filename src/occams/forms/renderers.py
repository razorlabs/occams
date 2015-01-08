"""
Renders HTML versions datastore forms.

Note that in order for these to work completely, clientside javascript
and associated plugins must be enabled.
"""

from __future__ import division

from pyramid.renderers import render
import six
import wtforms
import wtforms.fields.html5
import wtforms.widgets.html5
import wtforms.ext.dateutil.fields

from occams.forms import _, Session, models, log


def render_field(field, **kw):
    """
    Renders a wtform field with HTML5 attributes applied
    """
    if field.flags.required:
        kw['required'] = True
    # check validators Length, NumberRange or DateRange
    for validator in field.validators:
        if isinstance(validator, wtforms.validators.Length):
            # minlength is not supported by browsers
            if validator.min > -1:
                kw['minlength'] = validator.min
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


def strip_whitespace(value):
    """
    Strips a string of whitespace.
    Will result to None if the string is empty.
    """
    if value is not None:
        return value.strip() or None


def make_field(attribute):
    """
    Converts an attribute to a WTForm field
    """

    kw = {
        'label': attribute.title,
        'description': attribute.description,
        'filters': [],
        'validators': []
        }

    if attribute.type == 'section':

        class Section(wtforms.Form):
            pass

        for subattribute in attribute.itertraverse():
            setattr(Section, subattribute.name, make_field(subattribute))

        return wtforms.FormField(
            Section, label=attribute.title, description=attribute.description)

    elif attribute.type == 'number':
        if attribute.decimal_places == 0:
            field_class = wtforms.fields.html5.IntegerField
        else:
            field_class = wtforms.fields.html5.DecimalField
            if attribute.decimal_places > 0:
                ndigits = abs(attribute.decimal_places)
                step = round(1 / pow(10, ndigits), ndigits)
                kw['widget'] = wtforms.widgets.html5.NumberInput(step)

    elif attribute.type == 'string':
        field_class = wtforms.StringField
        kw['filters'].append(strip_whitespace)

        if attribute.widget == 'phone':
            kw['widget'] = wtforms.widgets.html5.TelInput()
        elif attribute.widget == 'email':
            kw['widget'] = wtforms.widgets.html5.EmailInput()

    elif attribute.type == 'text':
        field_class = wtforms.TextAreaField
        kw['filters'].append(strip_whitespace)

    elif attribute.type == 'date':
        field_class = wtforms.ext.dateutil.fields.DateField
        kw['widget'] = wtforms.widgets.html5.DateInput()

    elif attribute.type == 'datetime':
        field_class = wtforms.ext.dateutil.fields.DateTimeField
        kw['widget'] = wtforms.widgets.html5.DateTimeInput()

    elif attribute.type == 'choice':
        kw['choices'] = [(c.name, c.title) for c in attribute.iterchoices()]
        kw['coerce'] = lambda v: six.binary_type(v) if v is not None else None

        if attribute.is_collection:
            field_class = wtforms.SelectMultipleField
            if attribute.widget == 'select':
                kw['widget'] = wtforms.widgets.Select(multiple=True)
            else:
                kw['widget'] = wtforms.widgets.ListWidget(prefix_label=False)
                kw['option_widget'] = wtforms.widgets.CheckboxInput()
        else:
            field_class = wtforms.SelectField
            if attribute.widget == 'select':
                kw['widget'] = wtforms.widgets.Select()
            else:
                kw['widget'] = wtforms.widgets.ListWidget(prefix_label=False)
                kw['option_widget'] = wtforms.widgets.RadioInput()

    elif attribute.type == 'blob':
        field_class = wtforms.FileField

    else:
        raise Exception(u'Unknown type: %s' % attribute.type)

    if attribute.is_required:
        kw['validators'].append(wtforms.validators.InputRequired())
    else:
        kw['validators'].append(wtforms.validators.Optional())

    return field_class(**kw)


def make_form(schema, enable_metadata=True, allowed_versions=None):
    """
    Converts a Datastore schema to a WTForm.
    """

    class DatastoreForm(wtforms.Form):
        pass

    if enable_metadata:

        states = Session.query(models.State)

        if not allowed_versions:
            allowed_versions = []

        allowed_versions.append(schema.publish_date)
        allowed_versions = sorted(set(allowed_versions))

        actual_versions = [(v,) for v in (
            Session.query(models.Schema.publish_date)
            .filter(models.Schema.name == schema.name)
            .filter(models.Schema.publish_date.in_(allowed_versions))
            .order_by(models.publish_date.asc())
            .all())]

        if len(allowed_versions) != len(actual_versions):
            log.warn(
                'Inconsitent versions: %s != %s' % (
                    allowed_versions, actual_versions))

        class Metadata(wtforms.Form):
            status = wtforms.SelectField(_(u'Status'), choices=[
                (state.name, state.title) for state in states])
            not_done = wtforms.BooleanField(_(u'Not Done'))
            collect_date = wtforms.DateField(
                _(u'Collected'),
                validators=[wtforms.required()])
            version = wtforms.SelectField(
                _(u'Version'),
                choices=actual_versions,
                validators=[wtforms.required()])

        setattr(DatastoreForm, '__metadata__', wtforms.FormField(Metadata))

    for attribute in schema.itertraverse():
        setattr(DatastoreForm, attribute.name, make_field(attribute))

    return DatastoreForm


def make_longform(schemata):
    """
    Converts multiple Datastore schemata to a sinlge WTForm.
    """

    class LongForm(wtforms.Form):
        pass

    for schema in schemata:
        form = make_form(schema, enable_metadata=False)
        setattr(LongForm, schema.name, wtforms.FormField(form))

    return LongForm


def render_form(form, attr=None):
    """
    Helper function to render a WTForm by OCCAMS standards
    """
    return render('occams.forms:templates/form.pt', {
        'form': form,
        'attr': attr or {},
        })
