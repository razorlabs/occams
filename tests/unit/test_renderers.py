from ddt import ddt, data, unpack
from tests import IntegrationFixture
import wtforms.fields.html5
import wtforms.ext.dateutil.fields


class annotatedlist(list):
    pass


def expect_type(type_, class_):
    r = annotatedlist([type_, class_])
    setattr(r, '__name__', 'test_types_%s_to_%s' % (type_, class_.__name__))
    return r


@ddt
class TestMakeField(IntegrationFixture):

    def test_unknown(self):
        from occams_forms import models
        from occams_forms.renderers import make_field
        attribute = models.Attribute(name=u'f', title=u'F', type='unknown')
        with self.assertRaises(Exception):
            make_field(attribute)

    @data(
        expect_type('string', wtforms.StringField),
        expect_type('text', wtforms.TextAreaField),
        expect_type('blob', wtforms.FileField),
        expect_type('date', wtforms.ext.dateutil.fields.DateField),
        expect_type('datetime', wtforms.ext.dateutil.fields.DateTimeField),
        expect_type('section', wtforms.FormField))
    @unpack
    def test_basic_types(self, type_, class_):
        from occams_forms import models
        from occams_forms.renderers import make_field
        attribute = models.Attribute(name=u'f', title=u'F', type=type_)
        field = make_field(attribute)
        self.assertIs(field.field_class, class_)

    def test_integer(self):
        from occams_forms import models
        from occams_forms.renderers import make_field
        attribute = models.Attribute(
            name=u'f', title=u'F', type='number', decimal_places=0)
        field = make_field(attribute)
        self.assertIs(field.field_class, wtforms.fields.html5.IntegerField)

    def test_decimal_any(self):
        from occams_forms import models
        from occams_forms.renderers import make_field
        attribute = models.Attribute(name=u'f', title=u'F', type='number')
        field = make_field(attribute)
        self.assertIs(field.field_class, wtforms.fields.html5.DecimalField)

    def test_decimal_precision(self):
        from occams_forms import models
        from occams_forms.renderers import make_field
        attribute = models.Attribute(
            name=u'f', title=u'F', type='number', decimal_places=1)
        field = make_field(attribute)
        self.assertIs(field.field_class, wtforms.fields.html5.DecimalField)

    def test_choice_single(self):
        from occams_forms import models
        from occams_forms.renderers import make_field
        attribute = models.Attribute(
            name=u'f', title=u'F', type='choice', is_collection=False)
        field = make_field(attribute)
        self.assertIs(field.field_class, wtforms.SelectField)

    def test_choice_multi(self):
        from occams_forms import models
        from occams_forms.renderers import make_field
        attribute = models.Attribute(
            name=u'f', title=u'F', type='choice', is_collection=True)
        field = make_field(attribute)
        self.assertIs(field.field_class, wtforms.SelectMultipleField)
