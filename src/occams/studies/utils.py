from math import ceil

import six
import wtforms


def wtferrors(form):
    errors = {}

    def process(node):
        for key, field in node._fields.items():
            if isinstance(field, wtforms.FieldList):
                for entry in field.entries:
                    process(entry.form)
            elif isinstance(field, wtforms.FormField):
                process(field.form)
            else:
                if field.errors:
                    errors[field.id] = ' '.join(field.errors)

    process(form)
    return errors


class ModelField(wtforms.Field):

    widget = wtforms.widgets.TextInput()

    def __init__(self, *args, **kwargs):
        self.class_ = kwargs.pop('class_')
        self.session = kwargs.pop('session')
        super(ModelField, self).__init__(*args, **kwargs)

    def _value(self):
        return six.text_type(self.data.id) if self.data else u''

    def process_formdata(self, valuelist):
        if valuelist:
            try:
                id_ = int(valuelist[0])
            except ValueError:
                raise wtforms.ValidationError(self.gettext(u'Invalid value'))
            self.data = self.session.query(self.class_).get(id_)
            if not self.data:
                raise wtforms.ValidationError(self.gettext(u'Value not found'))
        else:
            self.data = None


class Pagination(object):
    """
    Pagination helper
    http://flask.pocoo.org/snippets/44/
    """

    def __init__(self, page, per_page, total_count):
        self.per_page = per_page
        self.total_count = total_count
        self.page = max(1, min(page, self.pages))

    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def offset(self):
        return (self.page - 1) * self.per_page

    @property
    def is_first(self):
        return self.page == 1

    @property
    def is_last(self):
        return self.page == self.pages

    @property
    def has_previous(self):
        return self.page > 1

    @property
    def previous_page(self):
        return max(1, self.page - 1)

    @property
    def has_next(self):
        return self.page < self.pages

    @property
    def next_page(self):
        return min(self.page + 1, self.pages)

    def serialize(self):
        return dict([(p, getattr(self, p)) for p in [
            'per_page',
            'page',
            'total_count',
            'pages', 'offset',
            'is_first', 'is_last',
            'has_previous', 'previous_page',
            'has_next', 'next_page']])

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num
