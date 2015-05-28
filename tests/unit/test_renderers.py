from ddt import ddt, data, unpack
import wtforms.fields.html5
import wtforms.ext.dateutil.fields

from tests import IntegrationFixture


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

    def test_string_min_max(self):
        from occams_forms import models
        from occams_forms.renderers import make_field
        import wtforms
        from wtforms.validators import Length
        attribute = models.Attribute(
            name=u'string_test', title=u'string_test', type='string',
            value_min=1, value_max=12)
        field = make_field(attribute)
        field = field.bind(wtforms.Form(), attribute.name)
        self.assertTrue(
            any(isinstance(v, Length) for v in field.validators))

    def test_number_min_max(self):
        from occams_forms import models
        from occams_forms.renderers import make_field
        import wtforms
        from wtforms.validators import NumberRange
        attribute = models.Attribute(
            name=u'number_test', title=u'number_test', type='number',
            value_min=1, value_max=12)
        field = make_field(attribute)
        field = field.bind(wtforms.Form(), attribute.name)
        self.assertTrue(
            any(isinstance(v, NumberRange) for v in field.validators))


class TestApplyData(IntegrationFixture):

    def setUp(self):
        super(TestApplyData, self).setUp()
        import tempfile
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def _call(self, *args, **kw):
        from occams_forms.renderers import apply_data
        return apply_data(*args, **kw)

    def _make_entity(self):
        from datetime import date
        from occams_forms import models
        schema = models.Schema(
            name=u'test', title=u'', publish_date=date.today(),
            attributes={
                'q1': models.Attribute(
                    name=u'q1',
                    title=u'',
                    type='string',
                    order=0,
                )
            })
        entity = models.Entity(schema=schema)
        return entity

    def test_clear_if_not_done(self):
        from datetime import date
        from occams_forms import Session

        entity = self._make_entity()
        entity['q1'] = u'Some value'

        formdata = {'ofmetadata_': {
            'not_done': True,
            'collect_date': date.today(),
            'version': entity.schema.publish_date
        }}

        self._call(Session, entity, formdata, self.tmpdir)

        self.assertIsNone(entity['q1'])

    def test_unknown_state_to_pending_entry(self):
        """
        It should clear data if transitioning to "Pending Entry"
        """
        from occams_forms import Session
        from occams_forms.renderers import states

        entity = self._make_entity()
        entity['q1'] = u'Some value'

        formdata = {
            'ofworkflow_': {
                'state': states.PENDING_ENTRY
            }
        }

        self._call(Session, entity, formdata, self.tmpdir)

        self.assertEquals(entity.state.name, states.PENDING_ENTRY)
        self.assertIsNone(entity['q1'])

    def test_pending_entry_to_pending_correction(self):
        from occams_forms import Session
        from occams_forms.renderers import states

        entity = self._make_entity()
        entity['q1'] = u'Some value'

        formdata = {
            'ofworkflow_': {
                'state': states.PENDING_CORRECTION,
            },
            'q1': u'Some new value'
        }

        self._call(Session, entity, formdata, self.tmpdir)

        self.assertEquals(entity.state.name, states.PENDING_CORRECTION)
        self.assertEquals(entity['q1'], formdata['q1'])

    def test_pending_entry_to_pending_review(self):
        from occams_forms import Session
        from occams_forms.renderers import states

        entity = self._make_entity()
        entity['q1'] = u'Some value'

        formdata = {
            'ofworkflow_': {
                'state': states.PENDING_REVIEW,
            },
            'q1': u'Some new value'
        }

        self._call(Session, entity, formdata, self.tmpdir)

        self.assertEquals(entity.state.name, states.PENDING_REVIEW)
        self.assertEquals(entity['q1'], formdata['q1'])

    def test_pending_entry_to_complete(self):
        from occams_forms import Session
        from occams_forms.renderers import states

        entity = self._make_entity()
        entity['q1'] = u'Some value'

        formdata = {
            'ofworkflow_': {
                'state': states.COMPLETE,
            },
            'q1': u'Some new value'
        }

        self._call(Session, entity, formdata, self.tmpdir)

        self.assertEquals(entity.state.name, states.COMPLETE)
        self.assertEquals(entity['q1'], formdata['q1'])

    def test_auto_pending_entry_to_pending_review(self):

        from occams_forms import Session
        from occams_forms.renderers import states

        entity = self._make_entity()
        entity['q1'] = u'Some value'

        formdata = {'q1': 'Some new value'}

        self._call(Session, entity, formdata, self.tmpdir)

        self.assertEquals(entity.state.name, states.PENDING_REVIEW)
        self.assertEqual(entity['q1'], formdata['q1'])

    def test_auto_pending_correction_to_pending_review(self):

        from occams_forms import Session, models
        from occams_forms.renderers import states

        entity = self._make_entity()
        entity.state = (
            Session.query(models.State)
            .filter_by(name=states.PENDING_CORRECTION)
            .one())
        entity['q1'] = u'Some value'

        formdata = {'q1': 'Some new value'}

        self._call(Session, entity, formdata, self.tmpdir)

        self.assertEquals(entity.state.name, states.PENDING_REVIEW)
        self.assertEqual(entity['q1'], formdata['q1'])
