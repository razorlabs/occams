"""
Renders HTML versions datastore forms.

Note that in order for these to work completely, clientside javascript
and associated plugins must be enabled.
"""

from __future__ import division
import collections
import os
import shutil
import tempfile
from itertools import groupby
import uuid

from pyramid.renderers import render
import six
import wtforms
import wtforms.fields.html5
import wtforms.widgets.html5
import wtforms.ext.dateutil.fields

from . import _, models, log


def version2json(schema):
    """
    Returns a single schema json record
    (this is how it's stored in the database)
    """
    data = {
        'id': schema.id,
        'name': schema.name,
        'title': schema.title,
        'publish_date': schema.publish_date.isoformat()}
    return data


def form2json(schemata):
    """
    Returns a representation of schemata grouped by versions.

    This is useful for representing schemata grouped by their version.

    The final dict contains the following values:
        ``schema`` -- a dict containing:
            ``name`` -- the schema name
            ``title`` -- the schema's most recent human title
        ``versions`` -- a list containining each version (see ``version2json``)

    This method accepts a single value (in which it will be transformted into
    a schema/versions pair, or a list which will be regrouped
    into schema/versions pairs
    """

    def by_name(schema):
        return schema.name

    def by_version(schema):
        return schema.publish_date

    def make_json(groups):
        groups = sorted(groups, key=by_version)
        return {
            'schema': {
                'name': groups[0].name,
                'title': groups[-1].title
                },
            'versions': list(map(version2json, groups))
            }

    if isinstance(schemata, collections.Iterable):
        schemata = sorted(schemata, key=by_name)
        return [make_json(g) for k, g in groupby(schemata, by_name)]
    elif isinstance(schemata, models.Schema):
        return make_json([schemata])


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

    if attribute.value_min or attribute.value_max:
        # for string min and max are used to test length
        if attribute.type == 'string':
            kw['validators'].append(wtforms.validators.Length(
                min=attribute.value_min,
                max=attribute.value_max))
        # for number min and max are used to test the value
        elif attribute.type == 'number':
            kw['validators'].append(wtforms.validators.NumberRange(
                min=attribute.value_min,
                max=attribute.value_max))

    if attribute.pattern:
        kw['validators'].append(wtforms.validators.Regexp(attribute.pattern))

    return field_class(**kw)


def make_form(session, schema, enable_metadata=True, allowed_versions=None):
    """
    Converts a Datastore schema to a WTForm.
    """

    class DatastoreForm(wtforms.Form):
        pass

    if enable_metadata:

        if not allowed_versions:
            allowed_versions = []

        allowed_versions.append(schema.publish_date)
        allowed_versions = sorted(set(allowed_versions))

        actual_versions = [(str(p), str(p)) for (p,) in (
            session.query(models.Schema.publish_date)
            .filter(models.Schema.name == schema.name)
            .filter(models.Schema.publish_date.in_(allowed_versions))
            .order_by(models.Schema.publish_date.asc())
            .all())]

        if len(allowed_versions) != len(actual_versions):
            log.warn(
                'Inconsitent versions: %s != %s' % (
                    allowed_versions, actual_versions))

        states = session.query(models.State)

        class Metadata(wtforms.Form):
            state = wtforms.SelectField(_(u'Status'), choices=[
                (state.name, state.title) for state in states])
            not_done = wtforms.BooleanField(_(u'Not Done'))
            collect_date = wtforms.ext.dateutil.fields.DateField(
                _(u'Collected'),
                widget=wtforms.widgets.html5.DateInput(),
                validators=[wtforms.validators.InputRequired()])
            version = wtforms.SelectField(
                _(u'Version'),
                choices=actual_versions,
                validators=[wtforms.validators.InputRequired()])

        setattr(DatastoreForm, 'ofmetadata_', wtforms.FormField(Metadata))

    for attribute in schema.itertraverse():
        setattr(DatastoreForm, attribute.name, make_field(attribute))

    return DatastoreForm


def make_longform(session, schemata):
    """
    Converts multiple Datastore schemata to a sinlge WTForm.
    """

    class LongForm(wtforms.Form):
        pass

    for schema in schemata:
        form = make_form(session, schema, enable_metadata=False)
        setattr(LongForm, schema.name, wtforms.FormField(form))

    return LongForm


def render_form(form, disabled=False, attr=None):
    """
    Helper function to render a WTForm by OCCAMS standards
    """
    return render('occams_forms:templates/form.pt', {
        'form': form,
        'disabled': disabled,
        'attr': attr or {},
        })


def entity_data(entity):
    data = {
        'ofmetadata_': {
            'state': entity.state and entity.state.name,
            'not_done': entity.not_done,
            'collect_date': entity.collect_date,
            'version': str(entity.schema.publish_date),
            }
        }
    for attribute in entity.schema.iterleafs():
        if attribute.parent_attribute:
            sub = data.setdefault(attribute.parent_attribute.name, {})
        else:
            sub = data
        sub[attribute.name] = entity[attribute.name]
    return data


def apply_data(session, entity, data, upload_path):
    """
    Updates an entity with a dictionary of data
    """

    assert upload_path is not None, u'Destination path is required'

    if 'ofmetadata_' in data:
        metadata = data['ofmetadata_']
        entity.state = (
            session.query(models.State)
            .filter_by(name=metadata['state'])
            .one())
        entity.not_done = metadata['not_done']
        entity.collect_date = metadata['collect_date']
        entity.schema = (
            session.query(models.Schema)
            .filter_by(
                name=entity.schema.name,
                publish_date=metadata['version'])
            .one())

    if upload_path is None:
        upload_path = tempfile.mkdtemp()
        try:
            apply_data(entity, data, upload_path)
        finally:
            shutil.rmtree(upload_path)
        return

    for attribute in entity.schema.iterleafs():

        # Find the appropriate sub-attribute to update
        if attribute.parent_attribute:
            sub = data[attribute.parent_attribute.name]
        else:
            sub = data

        # Accomodate patch data (i.e. incomplete data, for updates)
        if attribute.name not in sub:
            continue

        if attribute.type == 'blob':
            original_name = os.path.basename(data[attribute.name].filename)
            input_file = data[attribute.name].file

            generated_path = os.path.join(*str(uuid.uuid4()).split('-'))
            dest_path = os.path.join(upload_path, generated_path)

            # Write to a temporary file to prevent using incomplete files
            temp_dest_path = dest_path + '~'
            output_file = open(temp_dest_path, 'wb')

            input_file.seek(0)
            while True:
                data = input_file.read(2 << 16)
                if not data:
                    break
                output_file.write(data)

            # Make sure the data is commited to the file system before closing
            output_file.flush()
            os.fsync(output_file.fileno())

            output_file.close()

            # Rename successfully uploaded file
            os.rename(temp_dest_path, dest_path)

            mime_type = None

            value = models.BlobInfo(original_name, dest_path, mime_type)
        else:
            value = sub[attribute.name]

        entity[attribute.name] = value

    return entity
