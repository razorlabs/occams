import collections
from itertools import groupby

import six
import wtforms

from . import models


def wtferrors(form):
    errors = {}

    def inspect_field(field):
        if isinstance(field, wtforms.FormField):
            inspect_form(field.form)

        else:
            if isinstance(field, wtforms.FieldList):
                for entry in field.entries:
                    inspect_field(entry)

            if field.errors:
                # Ignore field enclosure's children's errors
                errors[field.id] = ' '.join(
                    e for e in field.errors if not isinstance(e, (list, dict)))

    def inspect_form(form):
        for key, field in form._fields.items():
            inspect_field(field)

    inspect_form(form)
    return errors


class ModelField(wtforms.Field):

    widget = wtforms.widgets.TextInput()

    _formdata = None

    def __init__(self, *args, **kwargs):
        self.class_ = kwargs.pop('class_')
        self.session = kwargs.pop('session')
        super(ModelField, self).__init__(*args, **kwargs)

    def _value(self):
        return six.text_type(self.data.id) if self.data else u''

    def process_formdata(self, valuelist):
        self.data = None
        # Keep a copy of the data until we can actually verify it
        self._formdata = valuelist[0] if valuelist else None

    def pre_validate(self, form):
        if self._formdata:
            try:
                id_ = int(self._formdata)
            except TypeError:
                raise wtforms.validators.StopValidation(
                    self.gettext(u'Invalid value'))
            else:
                self.data = self.session.query(self.class_).get(id_)
                if not self.data:
                    raise wtforms.validators.StopValidation(
                        self.gettext(u'Value not found'))


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
