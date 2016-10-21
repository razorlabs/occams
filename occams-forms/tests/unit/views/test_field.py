import pytest


@pytest.yield_fixture
def check_csrf_token():
    import mock
    name = 'occams_forms.views.field.check_csrf_token'
    with mock.patch(name) as patch:
        yield patch


class TestListJSON:

    def _call_fut(self, *args, **kw):
        from occams_forms.views.field import list_json
        return list_json(*args, **kw)

    def test_basic(self, req, db_session):
        """
        It should return a listing of a form's attributes and sections
        """
        from datetime import date
        from occams_datastore import models as datastore
        from occams_forms import models
        db_session.add(datastore.Schema(
            name=u'myform',
            title=u'My Form',
            publish_date=date(2014, 7, 1),
            attributes={
                'myfield': datastore.Attribute(
                    name=u'myfield',
                    title=u'My Field',
                    type=u'string',
                    order=0),
                'sec1': datastore.Attribute(
                    name=u'sec1',
                    title=u'Section 1',
                    type='section',
                    order=1,
                    attributes={
                        'mysubfield': datastore.Attribute(
                            name=u'mysubfield',
                            title=u'My Sub Field',
                            type=u'string',
                            order=2)})}))
        db_session.flush()
        res = self._call_fut(
            models.FormFactory(req)['myform']['versions']['2014-07-01']['fields'],
            req)
        assert 'fields' in res


class TestViewJSON:

    def _call_fut(self, *args, **kw):
        from occams_forms.views.field import view_json
        return view_json(*args, **kw)

    def test_basic(self, req, db_session):
        """
        It should return the attribute's properties in JSON form
        """
        from datetime import date
        from occams_datastore import models as datastore
        schema = datastore.Schema(
            name=u'myform',
            title=u'My Form',
            publish_date=date(2014, 7, 1),
            attributes={
                'myfield': datastore.Attribute(
                    name=u'myfield',
                    title=u'My Field',
                    type=u'string',
                    order=0)})
        db_session.add(schema)
        db_session.flush()
        res = self._call_fut(schema.attributes['myfield'], req)
        assert 'myfield' == res['name']


class TestEditJSON:

    def _call_fut(self, *args, **kw):
        from occams_forms.views.field import edit_json as view
        return view(*args, **kw)

    def test_add_duplicate_variable_name(
            self, req, db_session, check_csrf_token):
        """
        It should make sure the variable name is not repeated
        """
        from pyramid.httpexceptions import HTTPBadRequest
        from occams_datastore import models as datastore

        schema = datastore.Schema(
            name='testform',
            title=u'Test Form',
            attributes={
                'myvar': datastore.Attribute(
                    name='myvar',
                    title=u'My Var',
                    type='string',
                    order=0)
                })
        db_session.add(schema)
        db_session.flush()

        req.json_body = {'name': 'myvar'}

        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(schema['fields'], req)
        assert check_csrf_token.called
        assert 'name already exists' in \
            excinfo.value.json['errors']['name'].lower()

    def test_add_section_into_section(self, req, db_session, check_csrf_token):
        """
        It should not allow adding a new section into a another section
        """
        from pyramid.httpexceptions import HTTPBadRequest
        from occams_datastore import models as datastore

        schema = datastore.Schema(
            name='testform',
            title=u'Test Form',
            attributes={
                'section1': datastore.Attribute(
                    name='section1',
                    title=u'Section 1',
                    type='section',
                    order=0)
                })
        db_session.add(schema)
        db_session.flush()

        req.json_body = {
            'target': 'section1',
            'name': 'section2',
            'title': u'Section 2',
            'type': 'section'
        }

        with pytest.raises(HTTPBadRequest) as excinfo:
            self._call_fut(schema['fields'], req)

        assert 'nested sections are not supported' in \
            excinfo.value.json['errors']['target'].lower()


class TestMoveJSON:

    def _call_fut(self, *args, **kw):
        from occams_forms.views.field import move_json as view
        return view(*args, **kw)

    def _comparable(self, schema):
        """
        Helper function to convert a schema into a (section, name, order) tuple
        """
        return [(a.parent_attribute.name if a.parent_attribute else None,
                 a.name,
                 a.order
                 ) for a in schema.iterlist()]

    def test_from_section_to_schema(self, req, db_session, check_csrf_token):
        """
        It should be able to move a field from a section to the root
        """
        from occams_datastore import models as datastore

        schema = datastore.Schema(
            name='testform',
            title=u'Test Form',
            attributes={
                'section1': datastore.Attribute(
                    name='section1',
                    title=u'Section 1',
                    type='section',
                    attributes={
                        'myvar': datastore.Attribute(
                            name='myvar',
                            title=u'My Var',
                            type='string',
                            order=1)
                        },
                    order=0)
                })
        db_session.add(schema)
        db_session.flush()

        req.json_body = {
            'target': None,
            'index': 1
        }

        self._call_fut(schema.attributes['myvar'], req)

        assert sorted([(None, 'section1', 0), (None, 'myvar', 1)]) == \
            sorted(self._comparable(schema))

    def test_from_section_to_section(self, req, db_session, check_csrf_token):
        """
        It should be able to move a field from a section to another
        """
        from occams_datastore import models as datastore

        schema = datastore.Schema(
            name='testform',
            title=u'Test Form',
            attributes={
                'section1': datastore.Attribute(
                    name='section1',
                    title=u'Section 1',
                    type='section',
                    attributes={
                        'myvar': datastore.Attribute(
                            name='myvar',
                            title=u'My Var',
                            type='string',
                            order=1)
                        },
                    order=0),
                'section2': datastore.Attribute(
                    name='section2',
                    title=u'Section 2',
                    type='section',
                    order=2)
                })
        db_session.add(schema)
        db_session.flush()

        req.json_body = {
            'target': 'section2',
            'index': 0
        }

        self._call_fut(schema.attributes['myvar'], req)

        assert sorted([
            (None, 'section1', 0),
            (None, 'section2', 1),
            ('section2', 'myvar', 2)]) == \
            sorted(self._comparable(schema))

    def test_from_within_section(self, req, db_session, check_csrf_token):
        """
        It should be able to move a field within a section
        """
        from occams_datastore import models as datastore

        schema = datastore.Schema(
            name='testform',
            title=u'Test Form',
            attributes={
                'section1': datastore.Attribute(
                    name='section1',
                    title=u'Section 1',
                    type='section',
                    attributes={
                        'myvar': datastore.Attribute(
                            name='myvar',
                            title=u'My Var',
                            type='string',
                            order=1),
                        'myfoo': datastore.Attribute(
                            name='myfoo',
                            title=u'My Foo',
                            type='string',
                            order=2)
                        },
                    order=0),
                })
        db_session.add(schema)
        db_session.flush()

        req.json_body = {
            'target': 'section1',
            'index': 1
        }

        self._call_fut(schema.attributes['myvar'], req)

        assert sorted([
            (None, 'section1', 0),
            ('section1', 'myfoo', 1),
            ('section1', 'myvar', 2)]) == \
            sorted(self._comparable(schema))
