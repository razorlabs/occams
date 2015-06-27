"""
General form input utilities

Most of these utilities are to address short-comings of wtforms.
"""

import six
import wtforms


class Form(wtforms.Form):
    """
    Custom base form that automatically sanitizes form input
    """

    class Meta:

        def bind_field(self, form, unbound_field, options):
            filters = unbound_field.kwargs.get('filters', None) or []
            # WTForms doesn't let certain fields have filters
            if unbound_field.field_class \
                    not in (wtforms.FieldList, wtforms.FormField):
                filters.append(whitespace_filter)
            return unbound_field.bind(form=form, filters=filters, **options)


def whitespace_filter(value):
    """
    Strips white space from form input
    """

    return value.strip() if hasattr(value, 'strip') else value


def apply_changes(form, obj):
    """
    Apply changes to an object only if the value has changed

    Usefull for situations when we only want to apply expensive database
    flushes if the record has actually changed.
    """
    updated = []
    for name, field in six.iteritems(form._fields):
        if hasattr(obj, name) and getattr(obj, name) != field.data:
            setattr(obj, name, field.data)
            updated.append(name)
    return updated


def wtferrors(form):
    """
    Serializes form errors into a dictionary for client side validation.

    Addresses the fact that  Wtforms will not return the location within
    a ``ListField`` that caused a validation error.
    """
    errors = {}

    def inspect_field(field):
        if isinstance(field, wtforms.FormField):
            inspect_form(field.form)

        else:
            if isinstance(field, wtforms.FieldList):
                for entry in field.entries:
                    inspect_field(entry)

            # Only extract field-level messages (ignore sub-field errors)
            msgs = [e for e in field.errors if isinstance(e, six.string_types)]

            if msgs:
                errors[field.id] = ' '.join(msgs)

    def inspect_form(form):
        for key, field in form._fields.items():
            inspect_field(field)

    inspect_form(form)
    return errors


class ModelField(wtforms.Field):
    """
    SQLAlchemy model field
    """

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
