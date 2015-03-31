import six
import wtforms


def apply_changes(form, obj):
    updated = []
    for name, field in six.iteritems(form._fields):
        if hasattr(obj, name) and getattr(obj, name) != field.data:
            setattr(obj, name, field.data)
            updated.append(name)
    return updated


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
