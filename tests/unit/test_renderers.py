import pytest
import wtforms.fields.html5
import wtforms.ext.dateutil.fields

from occams_forms.fields import FileField


class TestMakeField:

    def test_unknown(self):
        from occams_forms import models
        from occams_forms.renderers import make_field
        attribute = models.Attribute(name=u'f', title=u'F', type='unknown')
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
        from occams_forms import models
        from occams_forms.renderers import make_field
        attribute = models.Attribute(name=u'f', title=u'F', type=type_)
        field = make_field(attribute)
        assert field.field_class is class_

    def test_integer(self):
        from occams_forms import models
        from occams_forms.renderers import make_field
        attribute = models.Attribute(
            name=u'f', title=u'F', type='number', decimal_places=0)
        field = make_field(attribute)
        assert field.field_class is wtforms.fields.html5.IntegerField

    def test_decimal_any(self):
        from occams_forms import models
        from occams_forms.renderers import make_field
        attribute = models.Attribute(name=u'f', title=u'F', type='number')
        field = make_field(attribute)
        assert field.field_class is wtforms.fields.html5.DecimalField

    def test_decimal_precision(self):
        from occams_forms import models
        from occams_forms.renderers import make_field
        attribute = models.Attribute(
            name=u'f', title=u'F', type='number', decimal_places=1)
        field = make_field(attribute)
        assert field.field_class is wtforms.fields.html5.DecimalField

    def test_choice_single(self):
        from occams_forms import models
        from occams_forms.renderers import make_field
        attribute = models.Attribute(
            name=u'f', title=u'F', type='choice', is_collection=False)
        field = make_field(attribute)
        assert field.field_class is wtforms.SelectField

    def test_choice_multi(self):
        from occams_forms import models
        from occams_forms.renderers import make_field
        attribute = models.Attribute(
            name=u'f', title=u'F', type='choice', is_collection=True)
        field = make_field(attribute)
        assert field.field_class is wtforms.SelectMultipleField

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
        assert any(isinstance(v, Length) for v in field.validators)

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
        assert any(isinstance(v, NumberRange) for v in field.validators)

    def test_daterange_date(self):
        from occams_forms import models
        from occams_forms.renderers import make_field
        import wtforms
        from wtforms_components import DateRange
        attribute = models.Attribute(
            name=u'daterange_test', title=u'daterange_test', type='date')
        field = make_field(attribute)
        field = field.bind(wtforms.Form(), attribute.name)
        assert any(isinstance(v, DateRange) for v in field.validators)

    def test_daterange_datetime(self):
        from occams_forms import models
        from occams_forms.renderers import make_field
        import wtforms
        from wtforms_components import DateRange
        attribute = models.Attribute(
            name=u'daterange_test', title=u'daterange_test', type='datetime')
        field = make_field(attribute)
        field = field.bind(wtforms.Form(), attribute.name)
        assert any(isinstance(v, DateRange) for v in field.validators)


class TestMakeForm:

    def _make_schema(self, db_session):
        from datetime import date
        from occams_forms import models
        schema = models.Schema(
            name=u'dymmy_schema',
            title=u'Dummy Schema',
            publish_date=date.today(),
            attributes={
                'dummy_field': models.Attribute(
                    name=u'dummy_field',
                    title=u'Dummy Field',
                    type='string',
                    is_required=True,
                    order=0
                )
            })

        db_session.add(schema)
        db_session.flush()

        return schema

    def test_skip_validation_if_to_pending_entry(self, db_session):
        from webob.multidict import MultiDict
        from occams_forms.renderers import make_form, states, modes

        schema = self._make_schema(db_session)
        Form = make_form(db_session, schema, transition=modes.ALL)
        form = Form(MultiDict({
            'ofworkflow_-state': states.PENDING_ENTRY,
        }))
        assert form.validate(), form.errors

    def test_skip_validation_if_from_complete(self, db_session):
        from webob.multidict import MultiDict
        from occams_forms import models
        from occams_forms.renderers import \
            make_form, states, modes, entity_data

        schema = self._make_schema(db_session)
        entity = models.Entity(
            schema=schema,
            state=(
                db_session.query(models.State)
                .filter_by(name=states.COMPLETE)
                .one()))
        Form = make_form(
            db_session, schema, entity=entity, transition=modes.ALL)
        formdata = MultiDict({
            'ofworkflow_-state': states.PENDING_CORRECTION,
        })
        form = Form(formdata, data=entity_data(entity))
        assert form.validate(), form.errors

    def test_skip_validation_if_not_collected(self, db_session):
        from datetime import date
        from webob.multidict import MultiDict
        from occams_forms.renderers import make_form

        schema = self._make_schema(db_session)
        Form = make_form(db_session, schema)

        form = Form(MultiDict({
            'ofmetadata_-collect_date': str(date.today()),
            'ofmetadata_-version': str(schema.publish_date),
            'ofmetadata_-not_done': '1',
        }))
        assert form.validate(), form.errors

    def test_validation_if_collected(self, db_session):
        from datetime import date
        from webob.multidict import MultiDict
        from occams_forms.renderers import make_form

        schema = self._make_schema(db_session)
        Form = make_form(db_session, schema)

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

    def _make_form(self, db_session):
        from datetime import date
        from occams_forms import models
        from occams_forms.renderers import make_form

        schema = models.Schema(
            name=u'dymmy_schema',
            title=u'Dummy Schema',
            publish_date=date.today(),
            attributes={
                'dummy_field': models.Attribute(
                    name=u'dummy_field',
                    title=u'Dummy Field',
                    type='string',
                    order=0
                )
            })

        entity = models.Entity(schema=schema)
        db_session.add(entity)
        db_session.flush()

        return make_form(db_session, schema, entity=entity)

    @pytest.mark.parametrize('state', [
        'pending-entry', 'pending-review', 'pending-correction'])
    def test_enabled_for_editable_states(self, db_session, state):

        from occams_forms import models
        from occams_forms.renderers import render_form
        from bs4 import BeautifulSoup

        Form = self._make_form(db_session)
        form = Form()

        form.meta.entity.state = (
            db_session.query(models.State)
            .filter_by(name=state)
            .one())

        markup = render_form(form)
        soup = BeautifulSoup(markup)

        field = soup.find(id='dummy_field')

        assert not field.has_attr('disabled')

    def test_disabled_if_complete(self, db_session):

        from occams_forms import models
        from occams_forms.renderers import render_form, states
        from bs4 import BeautifulSoup

        Form = self._make_form(db_session)
        form = Form()

        form.meta.entity.state = (
            db_session.query(models.State)
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
                    is_required=True,
                    order=0,
                )
            })
        entity = models.Entity(schema=schema)
        return entity

    def test_clear_if_not_done(self, db_session):
        from datetime import date

        entity = self._make_entity()
        entity['q1'] = u'Some value'

        formdata = {'ofmetadata_': {
            'not_done': True,
            'collect_date': date.today(),
            'version': entity.schema.publish_date
        }}

        self._call_fut(db_session, entity, formdata, self.tmpdir)

        assert entity['q1'] is None

    def test_clear_if_pending_entry(self, db_session):
        from datetime import date
        from occams_forms.renderers import states

        entity = self._make_entity()
        entity['q1'] = u'Some value'

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

        self._call_fut(db_session, entity, formdata, self.tmpdir)

        assert not entity.not_done
        assert entity['q1'] is None

    def test_unknown_state_to_pending_entry(self, db_session):
        """
        It should clear data if transitioning to "Pending Entry"
        """
        from occams_forms.renderers import states

        entity = self._make_entity()
        entity['q1'] = u'Some value'

        formdata = {
            'ofworkflow_': {
                'state': states.PENDING_ENTRY
            }
        }

        self._call_fut(db_session, entity, formdata, self.tmpdir)

        assert entity.state.name == states.PENDING_ENTRY
        assert entity['q1'] is None

    def test_pending_entry_to_pending_correction(self, db_session):
        from occams_forms.renderers import states

        entity = self._make_entity()
        entity['q1'] = u'Some value'

        formdata = {
            'ofworkflow_': {
                'state': states.PENDING_CORRECTION,
            },
            'q1': u'Some new value'
        }

        self._call_fut(db_session, entity, formdata, self.tmpdir)

        assert entity.state.name == states.PENDING_CORRECTION
        assert entity['q1'] == formdata['q1']

    def test_pending_entry_to_pending_review(self, db_session):
        from occams_forms.renderers import states

        entity = self._make_entity()
        entity['q1'] = u'Some value'

        formdata = {
            'ofworkflow_': {
                'state': states.PENDING_REVIEW,
            },
            'q1': u'Some new value'
        }

        self._call_fut(db_session, entity, formdata, self.tmpdir)

        assert entity.state.name == states.PENDING_REVIEW
        assert entity['q1'] == formdata['q1']

    def test_pending_entry_to_complete(self, db_session):
        from occams_forms.renderers import states

        entity = self._make_entity()
        entity['q1'] = u'Some value'

        formdata = {
            'ofworkflow_': {
                'state': states.COMPLETE,
            },
            'q1': u'Some new value'
        }

        self._call_fut(db_session, entity, formdata, self.tmpdir)

        assert entity.state.name == states.COMPLETE
        assert entity['q1'] == formdata['q1']

    def test_pending_review_to_complete(self, db_session):
        from occams_forms import models
        from occams_forms.renderers import states

        entity = self._make_entity()
        entity.state = (
            db_session.query(models.State)
            .filter_by(name=states.PENDING_REVIEW)
            .one())
        entity['q1'] = u'Some value'

        formdata = {
            'ofworkflow_': {
                'state': states.COMPLETE,
            },
            'q1': u'Last minute changes'
        }

        self._call_fut(db_session, entity, formdata, self.tmpdir)

        assert entity.state.name == states.COMPLETE
        assert entity['q1'] == formdata['q1']

    def test_auto_pending_entry_to_pending_review(self, db_session):

        from occams_forms.renderers import states

        entity = self._make_entity()
        entity['q1'] = u'Some value'

        formdata = {'q1': 'Some new value'}

        self._call_fut(db_session, entity, formdata, self.tmpdir)

        assert entity.state.name == states.PENDING_REVIEW
        assert entity['q1'] == formdata['q1']

    def test_auto_pending_correction_to_pending_review(self, db_session):

        from occams_forms import models
        from occams_forms.renderers import states

        entity = self._make_entity()
        entity.state = (
            db_session.query(models.State)
            .filter_by(name=states.PENDING_CORRECTION)
            .one())
        entity['q1'] = u'Some value'

        formdata = {'q1': 'Some new value'}

        self._call_fut(db_session, entity, formdata, self.tmpdir)

        assert entity.state.name == states.PENDING_REVIEW
        assert entity['q1'] == formdata['q1']

    def test_file_is_deleted(self, db_session):
        """
        Test file is deleted on the system after a non-FieldStorage
        object is passed to apply_data
        """

        import os
        from datetime import date

        from occams_forms import models

        from mock import Mock

        schema = models.Schema(
            name=u'test', title=u'', publish_date=date.today(),
            attributes={
                'q1': models.Attribute(
                    name=u'q1',
                    title=u'',
                    type='blob',
                    order=0
                )
            })

        entity = models.Entity(schema=schema)

        formdata = {'q1': u''}

        with open(os.path.join(self.tmpdir, 'test.txt'), 'w'):
            fullpath = os.path.join(self.tmpdir, 'test.txt')

        entity['q1'] = Mock(path=fullpath)

        self._call_fut(db_session, entity, formdata, self.tmpdir)
        assert not os.path.exists(fullpath)

    def test_previous_file_is_deleted(self, db_session):
        """
        Test if previous file is deleted from the
        system after a new non-FieldStoarage object
        is passed to apply_data
        """

        import os
        import cgi
        from datetime import date

        from occams_forms import models

        from mock import Mock

        schema = models.Schema(
            name=u'test', title=u'', publish_date=date.today(),
            attributes={
                'q1': models.Attribute(
                    name=u'q1',
                    title=u'',
                    type='blob',
                    order=0
                )
            })

        entity = models.Entity(schema=schema)

        form = cgi.FieldStorage()
        form.filename = u'test.txt'
        form.file = form.make_file()
        form.file.write(u'test_content')
        form.file.seek(0)

        formdata = {'q1': form}

        with open(os.path.join(self.tmpdir, 'test.txt'), 'w'):
            fullpath = os.path.join(self.tmpdir, 'test.txt')

        entity['q1'] = Mock(path=fullpath)

        self._call_fut(db_session, entity, formdata, self.tmpdir)

        formdata = {'q1': u''}
        self._call_fut(db_session, entity, formdata, self.tmpdir)
        assert not os.path.exists(fullpath)

    def test_old_file_is_deleted_after_update(self, db_session):
        """
        Test if previous file is deleted from the
        system after a new FieldStoarage object
        is passed to apply_data
        """
        import os
        import cgi
        from datetime import date

        from occams_forms import models

        from mock import Mock

        schema = models.Schema(
            name=u'test', title=u'', publish_date=date.today(),
            attributes={
                'q1': models.Attribute(
                    name=u'q1',
                    title=u'',
                    type='blob',
                    order=0
                )
            })

        entity = models.Entity(schema=schema)

        form = cgi.FieldStorage()
        form.filename = u'test.txt'
        form.file = form.make_file()
        form.file.write(u'test_content')
        form.file.seek(0)

        formdata = {'q1': form}

        with open(os.path.join(self.tmpdir, 'test.txt'), 'w'):
            fullpath = os.path.join(self.tmpdir, 'test.txt')

        entity['q1'] = Mock(path=fullpath)

        self._call_fut(db_session, entity, formdata, self.tmpdir)

        form_update = cgi.FieldStorage()
        form_update.filename = u'test2.txt'
        form_update.file = form.make_file()
        form_update.file.write(u'test_content')
        form_update.file.seek(0)

        formdata2 = {'q1': form_update}
        self._call_fut(db_session, entity, formdata2, self.tmpdir)

        assert not os.path.exists(fullpath)

    def test_file_is_inserted_to_db(self, db_session):
        """
        Test if a new record is inserted to value_blob
        table after a FieldStorage object is passed to apply_data
        """

        import os
        import cgi
        from datetime import date

        from occams_forms import models
        from occams_datastore import models as datastore

        from mock import Mock

        schema = models.Schema(
            name=u'test', title=u'', publish_date=date.today(),
            attributes={
                'q1': models.Attribute(
                    name=u'q1',
                    title=u'',
                    type='blob',
                    order=0
                )
            })

        entity = models.Entity(schema=schema)

        form = cgi.FieldStorage()
        form.filename = u'test.txt'
        form.file = form.make_file()
        form.file.write(u'test_content')
        form.file.seek(0)

        formdata = {'q1': form}

        with open(os.path.join(self.tmpdir, 'test.txt'), 'w'):
            fullpath = os.path.join(self.tmpdir, 'test.txt')

        entity['q1'] = Mock(path=fullpath)

        self._call_fut(db_session, entity, formdata, self.tmpdir)

        blob = db_session.query(datastore.ValueBlob).filter_by(
            file_name=u'test.txt').one()
        assert blob.file_name == u'test.txt'

    def test_old_file_is_deleted_db_after_empty_string_applied(
            self, db_session):
        """
        Test if previous file is deleted from db after
        a non-FieldStoarage is passed to apply_data
        """

        import os
        import cgi
        from datetime import date

        from occams_forms import models
        from occams_datastore import models as datastore

        from mock import Mock

        schema = models.Schema(
            name=u'test', title=u'', publish_date=date.today(),
            attributes={
                'q1': models.Attribute(
                    name=u'q1',
                    title=u'',
                    type='blob',
                    order=0
                )
            })

        entity = models.Entity(schema=schema)

        form = cgi.FieldStorage()
        form.filename = u'test.txt'
        form.file = form.make_file()
        form.file.write(u'test_content')
        form.file.seek(0)

        formdata = {'q1': form}

        with open(os.path.join(self.tmpdir, 'test.txt'), 'w'):
            fullpath = os.path.join(self.tmpdir, 'test.txt')

        entity['q1'] = Mock(path=fullpath)

        self._call_fut(db_session, entity, formdata, self.tmpdir)

        formdata = {'q1': u''}
        self._call_fut(db_session, entity, formdata, self.tmpdir)

        blob = db_session.query(datastore.ValueBlob).filter_by(
            file_name=u'test.txt').first()

        assert blob is None

    def test_one_record_exists_db_after_update(self, db_session):
        """
        Test if one updated record exists in value_blob tbl
        after FieldStorage object passed to apply_data
        """

        import os
        import cgi
        from datetime import date

        from occams_forms import models
        from occams_datastore import models as datastore

        from mock import Mock

        schema = models.Schema(
            name=u'test', title=u'', publish_date=date.today(),
            attributes={
                'q1': models.Attribute(
                    name=u'q1',
                    title=u'',
                    type='blob',
                    order=0
                )
            })

        entity = models.Entity(schema=schema)

        form = cgi.FieldStorage()
        form.filename = u'test.txt'
        form.file = form.make_file()
        form.file.write(u'test_content')
        form.file.seek(0)

        formdata = {'q1': form}

        with open(os.path.join(self.tmpdir, 'test.txt'), 'w'):
            fullpath = os.path.join(self.tmpdir, 'test.txt')

        entity['q1'] = Mock(path=fullpath)

        self._call_fut(db_session, entity, formdata, self.tmpdir)

        blob = db_session.query(datastore.ValueBlob).one()
        entity_id = blob.entity.id

        form_update = cgi.FieldStorage()
        form_update.filename = u'test2.txt'
        form_update.file = form.make_file()
        form_update.file.write(u'test_content')
        form_update.file.seek(0)

        formdata2 = {'q1': form_update}
        self._call_fut(db_session, entity, formdata2, self.tmpdir)

        blob = db_session.query(datastore.ValueBlob).filter_by(
            file_name=u'test2.txt').first()
        entity_id_after_update = blob.entity_id
        assert entity_id == entity_id_after_update
