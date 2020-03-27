import pytest
import wtforms.fields.html5
import wtforms.ext.dateutil.fields

from occams.fields import FileField


class TestMakeField:

    def test_unknown(self):
        from occams import models
        from occams.renderers import make_field
        attribute = models.Attribute(name='f', title='F', type='unknown')
        with pytest.raises(Exception):
            make_field(attribute)

    @pytest.mark.parametrize('type_,class_', [
        ('string', wtforms.StringField),
        ('text', wtforms.TextAreaField),
        ('blob', FileField),
        ('date', wtforms.ext.dateutil.fields.DateField),
        ('datetime', wtforms.ext.dateutil.fields.DateTimeField),
        ('section', wtforms.FormField)])
    def test_basic_types(self, type_, class_):
        from occams import models
        from occams.renderers import make_field
        attribute = models.Attribute(name='f', title='F', type=type_)
        field = make_field(attribute)
        assert field.field_class is class_

    def test_integer(self):
        from occams import models
        from occams.renderers import make_field
        attribute = models.Attribute(
            name='f', title='F', type='number', decimal_places=0)
        field = make_field(attribute)
        assert field.field_class is wtforms.fields.html5.IntegerField

    def test_decimal_any(self):
        from occams import models
        from occams.renderers import make_field
        attribute = models.Attribute(name='f', title='F', type='number')
        field = make_field(attribute)
        assert field.field_class is wtforms.fields.html5.DecimalField

    def test_decimal_precision(self):
        from occams import models
        from occams.renderers import make_field
        attribute = models.Attribute(
            name='f', title='F', type='number', decimal_places=1)
        field = make_field(attribute)
        assert field.field_class is wtforms.fields.html5.DecimalField
        assert field.kwargs['places'] == 1
        assert field.kwargs['rounding'] == 'ROUND_UP'

    def test_choice_single(self):
        from occams import models
        from occams.renderers import make_field
        attribute = models.Attribute(
            name='f', title='F', type='choice', is_collection=False)
        field = make_field(attribute)
        assert field.field_class is wtforms.SelectField

    def test_choice_multi(self):
        from occams import models
        from occams.renderers import make_field
        attribute = models.Attribute(
            name='f', title='F', type='choice', is_collection=True)
        field = make_field(attribute)
        assert field.field_class is wtforms.SelectMultipleField

    def test_string_min_max(self):
        from occams import models
        from occams.renderers import make_field
        import wtforms
        from wtforms.validators import Length
        attribute = models.Attribute(
            name='string_test', title='string_test', type='string',
            value_min=1, value_max=12)
        field = make_field(attribute)
        field = field.bind(wtforms.Form(), attribute.name)
        assert any(isinstance(v, Length) for v in field.validators)

    def test_string_min_max_same_value(self):
        from occams import models
        from occams.renderers import make_field
        import wtforms
        from wtforms.validators import Length
        attribute = models.Attribute(
            name='string_test', title='string_test', type='string',
            value_min=3, value_max=3)
        field = make_field(attribute)
        field = field.bind(wtforms.Form(), attribute.name)
        assert any(isinstance(v, Length) for v in field.validators)

    def test_multiple_choice_min_max(self):
        from occams import models
        from occams.renderers import make_field
        import wtforms
        from wtforms.validators import Length
        attribute = models.Attribute(
            name='choice', title='choice_test', type='choice',
            is_collection=True,
            value_min=1, value_max=12)
        field = make_field(attribute)
        field = field.bind(wtforms.Form(), attribute.name)
        assert any(isinstance(v, Length) for v in field.validators)

    def test_multiple_choice_min_max_same_value(self):
        from occams import models
        from occams.renderers import make_field
        import wtforms
        from wtforms.validators import Length
        attribute = models.Attribute(
            name='choice', title='choice_test', type='choice',
            is_collection=True,
            value_min=3, value_max=3)
        field = make_field(attribute)
        field = field.bind(wtforms.Form(), attribute.name)
        assert any(isinstance(v, Length) for v in field.validators)

    def test_number_min_max(self):
        from occams import models
        from occams.renderers import make_field
        import wtforms
        from wtforms.validators import NumberRange
        attribute = models.Attribute(
            name='number_test', title='number_test', type='number',
            value_min=1, value_max=12)
        field = make_field(attribute)
        field = field.bind(wtforms.Form(), attribute.name)
        assert any(isinstance(v, NumberRange) for v in field.validators)

    def test_number_min_max_same_number(self):
        from occams import models
        from occams.renderers import make_field
        import wtforms
        from wtforms.validators import NumberRange
        attribute = models.Attribute(
            name='number_test', title='number_test', type='number',
            value_min=3, value_max=3)
        field = make_field(attribute)
        field = field.bind(wtforms.Form(), attribute.name)
        assert any(isinstance(v, NumberRange) for v in field.validators)

    def test_daterange_date(self):
        from occams import models
        from occams.renderers import make_field
        import wtforms
        from wtforms_components import DateRange
        attribute = models.Attribute(
            name='daterange_test', title='daterange_test', type='date')
        field = make_field(attribute)
        field = field.bind(wtforms.Form(), attribute.name)
        assert any(isinstance(v, DateRange) for v in field.validators)

    def test_daterange_datetime(self):
        from occams import models
        from occams.renderers import make_field
        import wtforms
        from wtforms_components import DateRange
        attribute = models.Attribute(
            name='daterange_test', title='daterange_test', type='datetime')
        field = make_field(attribute)
        field = field.bind(wtforms.Form(), attribute.name)
        assert any(isinstance(v, DateRange) for v in field.validators)


class TestMakeForm:

    def _make_schema(self, dbsession):
        from datetime import date
        from occams import models
        schema = models.Schema(
            name='dymmy_schema',
            title='Dummy Schema',
            publish_date=date.today(),
            attributes={
                'dummy_field': models.Attribute(
                    name='dummy_field',
                    title='Dummy Field',
                    type='string',
                    is_required=True,
                    order=0
                )
            })

        dbsession.add(schema)
        dbsession.flush()

        return schema

    def test_skip_validation_if_to_pending_entry(self, dbsession):
        from webob.multidict import MultiDict
        from occams.renderers import make_form, states, modes

        schema = self._make_schema(dbsession)
        Form = make_form(dbsession, schema, transition=modes.ALL)
        form = Form(MultiDict({
            'ofworkflow_-state': states.PENDING_ENTRY,
        }))
        assert form.validate(), form.errors

    def test_skip_validation_if_from_complete(self, dbsession):
        from webob.multidict import MultiDict
        from occams import models
        from occams.renderers import \
            make_form, states, modes, entity_data

        schema = self._make_schema(dbsession)
        entity = models.Entity(
            schema=schema,
            state=(
                dbsession.query(models.State)
                .filter_by(name=states.COMPLETE)
                .one()))
        Form = make_form(
            dbsession, schema, entity=entity, transition=modes.ALL)
        formdata = MultiDict({
            'ofworkflow_-state': states.PENDING_CORRECTION,
        })
        form = Form(formdata, data=entity_data(entity))
        assert form.validate(), form.errors

    def test_skip_validation_if_not_collected(self, dbsession):
        from datetime import date
        from webob.multidict import MultiDict
        from occams.renderers import make_form

        schema = self._make_schema(dbsession)
        Form = make_form(dbsession, schema)

        form = Form(MultiDict({
            'ofmetadata_-collect_date': str(date.today()),
            'ofmetadata_-version': str(schema.publish_date),
            'ofmetadata_-not_done': '1',
        }))
        assert form.validate(), form.errors

    def test_validation_if_collected(self, dbsession):
        from datetime import date
        from webob.multidict import MultiDict
        from occams.renderers import make_form

        schema = self._make_schema(dbsession)
        Form = make_form(dbsession, schema)

        form = Form(MultiDict({
            'ofmetadata_-collect_date': str(date.today()),
            'ofmetadata_-version': str(schema.publish_date),
            'ofmetadata_-not_done': '',
        }))

        assert not form.validate()
        assert 'dummy_field' in form.errors


class TestRenderForm:

    @pytest.fixture(autouse=True)
    def include_templating(self, config):
        config.include('pyramid_chameleon')

    def _make_form(self, dbsession):
        from datetime import date
        from occams import models
        from occams.renderers import make_form

        schema = models.Schema(
            name='dymmy_schema',
            title='Dummy Schema',
            publish_date=date.today(),
            attributes={
                'dummy_field': models.Attribute(
                    name='dummy_field',
                    title='Dummy Field',
                    type='string',
                    order=0
                )
            })

        entity = models.Entity(schema=schema)
        dbsession.add(entity)
        dbsession.flush()

        return make_form(dbsession, schema, entity=entity)

    @pytest.mark.parametrize('state', [
        'pending-entry', 'pending-review', 'pending-correction'])
    def test_enabled_for_editable_states(self, dbsession, state):

        from occams import models
        from occams.renderers import render_form
        from bs4 import BeautifulSoup

        Form = self._make_form(dbsession)
        form = Form()

        form.meta.entity.state = (
            dbsession.query(models.State)
            .filter_by(name=state)
            .one())

        markup = render_form(form)
        soup = BeautifulSoup(markup)

        field = soup.find(id='dummy_field')

        assert not field.has_attr('disabled')

    def test_disabled_if_complete(self, dbsession):

        from occams import models
        from occams.renderers import render_form, states
        from bs4 import BeautifulSoup

        Form = self._make_form(dbsession)
        form = Form()

        form.meta.entity.state = (
            dbsession.query(models.State)
            .filter_by(name=states.COMPLETE)
            .one())

        markup = render_form(form)
        soup = BeautifulSoup(markup)

        field = soup.find(id='dummy_field')

        assert field.has_attr('disabled')


class TestApplyData:

    @pytest.fixture(autouse=True)
    def tmpdir(self, request):
        import tempfile
        import shutil
        self.tmpdir = tempfile.mkdtemp()

        def rm():
            shutil.rmtree(self.tmpdir)

        request.addfinalizer(rm)

    def _call_fut(self, *args, **kw):
        from occams.renderers import apply_data
        return apply_data(*args, **kw)

    def _make_entity(self):
        from datetime import date
        from occams import models
        schema = models.Schema(
            name='test', title='', publish_date=date.today(),
            attributes={
                'q1': models.Attribute(
                    name='q1',
                    title='',
                    type='string',
                    is_required=True,
                    order=0,
                )
            })
        entity = models.Entity(schema=schema)
        return entity

    def test_clear_if_not_done(self, dbsession):
        from datetime import date

        entity = self._make_entity()
        entity['q1'] = 'Some value'

        formdata = {'ofmetadata_': {
            'not_done': True,
            'collect_date': date.today(),
            'version': entity.schema.publish_date
        }}

        self._call_fut(dbsession, entity, formdata, self.tmpdir)

        assert entity['q1'] is None

    def test_clear_if_pending_entry(self, dbsession):
        from datetime import date
        from occams.renderers import states

        entity = self._make_entity()
        entity['q1'] = 'Some value'

        formdata = {
            'ofmetadata_': {
                'not_done': True,
                'collect_date': date.today(),
                'version': entity.schema.publish_date
            },
            'ofworkflow_': {
                'state': states.PENDING_ENTRY
            }
        }

        self._call_fut(dbsession, entity, formdata, self.tmpdir)

        assert not entity.not_done
        assert entity['q1'] is None

    def test_unknown_state_to_pending_entry(self, dbsession):
        """
        It should clear data if transitioning to "Pending Entry"
        """
        from occams.renderers import states

        entity = self._make_entity()
        entity['q1'] = 'Some value'

        formdata = {
            'ofworkflow_': {
                'state': states.PENDING_ENTRY
            }
        }

        self._call_fut(dbsession, entity, formdata, self.tmpdir)

        assert entity.state.name == states.PENDING_ENTRY
        assert entity['q1'] is None

    def test_pending_entry_to_pending_correction(self, dbsession):
        from occams.renderers import states

        entity = self._make_entity()
        entity['q1'] = 'Some value'

        formdata = {
            'ofworkflow_': {
                'state': states.PENDING_CORRECTION,
            },
            'q1': 'Some new value'
        }

        self._call_fut(dbsession, entity, formdata, self.tmpdir)

        assert entity.state.name == states.PENDING_CORRECTION
        assert entity['q1'] == formdata['q1']

    def test_pending_entry_to_pending_review(self, dbsession):
        from occams.renderers import states

        entity = self._make_entity()
        entity['q1'] = 'Some value'

        formdata = {
            'ofworkflow_': {
                'state': states.PENDING_REVIEW,
            },
            'q1': 'Some new value'
        }

        self._call_fut(dbsession, entity, formdata, self.tmpdir)

        assert entity.state.name == states.PENDING_REVIEW
        assert entity['q1'] == formdata['q1']

    def test_pending_entry_to_complete(self, dbsession):
        from occams.renderers import states

        entity = self._make_entity()
        entity['q1'] = 'Some value'

        formdata = {
            'ofworkflow_': {
                'state': states.COMPLETE,
            },
            'q1': 'Some new value'
        }

        self._call_fut(dbsession, entity, formdata, self.tmpdir)

        assert entity.state.name == states.COMPLETE
        assert entity['q1'] == formdata['q1']

    def test_pending_review_to_complete(self, dbsession):
        from occams import models
        from occams.renderers import states

        entity = self._make_entity()
        entity.state = (
            dbsession.query(models.State)
            .filter_by(name=states.PENDING_REVIEW)
            .one())
        entity['q1'] = 'Some value'

        formdata = {
            'ofworkflow_': {
                'state': states.COMPLETE,
            },
            'q1': 'Last minute changes'
        }

        self._call_fut(dbsession, entity, formdata, self.tmpdir)

        assert entity.state.name == states.COMPLETE
        assert entity['q1'] == formdata['q1']

    def test_auto_pending_entry_to_pending_review(self, dbsession):

        from occams.renderers import states

        entity = self._make_entity()
        entity['q1'] = 'Some value'

        formdata = {'q1': 'Some new value'}

        self._call_fut(dbsession, entity, formdata, self.tmpdir)

        assert entity.state.name == states.PENDING_REVIEW
        assert entity['q1'] == formdata['q1']

    def test_auto_pending_correction_to_pending_review(self, dbsession):

        from occams import models
        from occams.renderers import states

        entity = self._make_entity()
        entity.state = (
            dbsession.query(models.State)
            .filter_by(name=states.PENDING_CORRECTION)
            .one())
        entity['q1'] = 'Some value'

        formdata = {'q1': 'Some new value'}

        self._call_fut(dbsession, entity, formdata, self.tmpdir)

        assert entity.state.name == states.PENDING_REVIEW
        assert entity['q1'] == formdata['q1']

    def test_file_is_deleted(self, dbsession):
        """
        Test file is deleted on the system after a non-FieldStorage
        object is passed to apply_data
        """

        import os
        from datetime import date

        from occams import models

        schema = models.Schema(
            name='test', title='', publish_date=date.today(),
            attributes={
                'q1': models.Attribute(
                    name='q1',
                    title='',
                    type='blob',
                    order=0
                )
            })

        entity = models.Entity(schema=schema)

        formdata = {'q1': ''}

        self._call_fut(dbsession, entity, formdata, self.tmpdir)
        assert len(entity.attachments) == 0

    def test_previous_file_is_deleted(self, dbsession):
        """
        Test if previous file is deleted from the
        system after a new non-FieldStoarage object
        is passed to apply_data
        """

        import os
        import cgi
        from datetime import date

        from occams import models

        schema = models.Schema(
            name='test', title='', publish_date=date.today(),
            attributes={
                'q1': models.Attribute(
                    name='q1',
                    title='',
                    type='blob',
                    order=0
                )
            })

        entity = models.Entity(schema=schema)

        form = cgi.FieldStorage()
        form._binary_file = True
        form.filename = 'test.txt'
        form.file = form.make_file()
        form.file.write(b'test_content')
        form.file.seek(0)
        formdata = {'q1': form}
        self._call_fut(dbsession, entity, formdata, self.tmpdir)

        formdata = {'q1': ''}
        self._call_fut(dbsession, entity, formdata, self.tmpdir)

        assert len(entity.attachments) == 0

    def test_old_file_is_deleted_after_update(self, dbsession):
        """
        Test if previous file is deleted from the
        system after a new FieldStoarage object
        is passed to apply_data
        """
        import os
        import cgi
        from datetime import date

        from occams import models

        schema = models.Schema(
            name='test', title='', publish_date=date.today(),
            attributes={
                'q1': models.Attribute(
                    name='q1',
                    title='',
                    type='blob',
                    order=0
                )
            })

        entity = models.Entity(schema=schema)

        form = cgi.FieldStorage()
        form._binary_file = True
        form.filename = 'test.txt'
        form.file = form.make_file()
        form.file.write(b'test_content')
        form.file.seek(0)
        formdata = {'q1': form}
        self._call_fut(dbsession, entity, formdata, self.tmpdir)

        assert entity.attachments[ entity['q1'] ].file_name == 'test.txt'

    def test_old_file_is_deleted_db_after_empty_string_applied(
            self, dbsession):
        """
        Test if previous file is deleted from db after
        a non-FieldStoarage is passed to apply_data
        """

        import os
        import cgi
        from datetime import date

        from occams import models

        schema = models.Schema(
            name='test', title='', publish_date=date.today(),
            attributes={
                'q1': models.Attribute(
                    name='q1',
                    title='',
                    type='blob',
                    order=0
                )
            })

        entity = models.Entity(schema=schema)

        form = cgi.FieldStorage()
        form._binary_file = True
        form.filename = 'test1.txt'
        form.file = form.make_file()
        form.file.write(b'test_content')
        form.file.seek(0)
        formdata = {'q1' : form}
        self._call_fut(dbsession, entity, formdata, self.tmpdir)

        formdata = {'q1': ''}
        self._call_fut(dbsession, entity, formdata, self.tmpdir)

        assert len(entity.attachments) == 0
        assert entity['q1'] is None

    def test_one_record_exists_db_after_update(self, dbsession):
        """
        Test if one updated record exists in value_blob tbl
        after FieldStorage object passed to apply_data
        """

        import os
        import cgi
        from datetime import date
        import tempfile

        from occams import models

        schema = models.Schema(
            name='test', title='', publish_date=date.today(),
            attributes={
                'q1': models.Attribute(
                    name='q1',
                    title='',
                    type='blob',
                    order=0
                )
            })

        entity = models.Entity(schema=schema)
        dbsession.add(entity)
        dbsession.flush()

        form = cgi.FieldStorage()
        form._binary_file = True
        form.filename = 'test1.txt'
        form.file = form.make_file()
        form.file.write(b'test_content')
        form.file.seek(0)
        formdata = {'q1': form}
        self._call_fut(dbsession, entity, formdata, self.tmpdir)

        form_update = cgi.FieldStorage()
        form._binary_file = True
        form_update.filename = 'test2.txt'
        form_update.file = form.make_file()
        form_update.file.write(b'test_content')
        form_update.file.seek(0)
        formdata2 = {'q1': form_update}
        self._call_fut(dbsession, entity, formdata2, self.tmpdir)

        assert len(entity.attachments) == 1
        assert entity.attachments[ entity['q1'] ].file_name == 'test2.txt'
