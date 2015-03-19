import mock

from tests import IntegrationFixture


class TestListJSON(IntegrationFixture):

    def _call_view(self, context, request):
        from occams.forms.views.field import list_json
        return list_json(context, request)

    def test_basic(self):
        """
        It should return a listing of a form's attributes and sections
        """
        from datetime import date
        from pyramid import testing
        from occams.forms import Session, models
        self.config.add_route('fields', '/fields')
        self.config.add_route('field', '/field/{field}')
        Session.add(models.Schema(
            name=u'myform',
            title=u'My Form',
            publish_date=date(2014, 7, 1),
            attributes={
                'myfield': models.Attribute(
                    name=u'myfield',
                    title=u'My Field',
                    type=u'string',
                    order=0),
                'sec1': models.Attribute(
                    name=u'sec1',
                    title=u'Section 1',
                    type='section',
                    order=1,
                    attributes={
                        'mysubfield': models.Attribute(
                            name=u'mysubfield',
                            title=u'My Sub Field',
                            type=u'string',
                            order=2)})}))
        Session.flush()
        request = testing.DummyRequest()
        response = self._call_view(
            models.FormFactory(request)['myform']['versions']['2014-07-01']['fields'],
            request)
        self.assertIn('fields', response)


class TestViewJSON(IntegrationFixture):

    def _call_view(self, context, request):
        from occams.forms.views.field import view_json
        return view_json(context, request)

    def test_basic(self):
        """
        It should return the attribute's properties in JSON form
        """
        from datetime import date
        from pyramid import testing
        from occams.forms import Session, models
        self.config.add_route('field', '/field/{field}')
        schema = models.Schema(
            name=u'myform',
            title=u'My Form',
            publish_date=date(2014, 7, 1),
            attributes={
                'myfield': models.Attribute(
                    name=u'myfield',
                    title=u'My Field',
                    type=u'string',
                    order=0)})
        Session.add(schema)
        Session.flush()
        response = self._call_view(
            schema.attributes['myfield'],
            testing.DummyRequest())
        self.assertEqual('myfield', response['name'])


@mock.patch('occams.forms.views.field.check_csrf_token')
class TestEditJSON(IntegrationFixture):

    def _call_view(self, context, request):
        from occams.forms.views.field import edit_json as view
        return view(context, request)

    def test_add_duplicate_variable_name(self, check_csrf_token):
        """
        It should make sure the variable name is not repeated
        """
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams.forms import models, Session

        schema = models.Schema(
            name='testform',
            title=u'Test Form',
            attributes={
                'myvar': models.Attribute(
                    name='myvar',
                    title=u'My Var',
                    type='string',
                    order=0)
                })
        Session.add(schema)
        Session.flush()

        request = testing.DummyRequest(json_body={'name': 'myvar'})

        with self.assertRaises(HTTPBadRequest) as cm:
            self._call_view(schema['fields'], request)
        self.assertTrue(check_csrf_token.called)
        self.assertIn(
            'name already exists', cm.exception.json['errors']['name'].lower())

    def test_add_section_into_section(self, check_csrf_token):
        """
        It should not allow adding a new section into a another section
        """
        from pyramid import testing
        from pyramid.httpexceptions import HTTPBadRequest
        from occams.forms import models, Session

        schema = models.Schema(
            name='testform',
            title=u'Test Form',
            attributes={
                'section1': models.Attribute(
                    name='section1',
                    title=u'Section 1',
                    type='section',
                    order=0)
                })
        Session.add(schema)
        Session.flush()

        request = testing.DummyRequest(json_body={
            'target': 'section1',
            'name': 'section2',
            'title': u'Section 2',
            'type': 'section'})

        with self.assertRaises(HTTPBadRequest) as cm:
            self._call_view(schema['fields'], request)

        self.assertIn(
            'nested sections are not supported',
            cm.exception.json['errors']['target'].lower())


@mock.patch('occams.forms.views.field.check_csrf_token')
class TestMoveJSON(IntegrationFixture):

    def _call_view(self, context, request):
        from occams.forms.views.field import move_json as view
        return view(context, request)

    def _comparable(self, schema):
        """
        Helper function to convert a schema into a (section, name, order) tuple
        """
        return [(a.parent_attribute.name if a.parent_attribute else None,
                 a.name,
                 a.order
                 ) for a in schema.iterlist()]

    def test_from_section_to_schema(self, check_csrf_token):
        """
        It should be able to move a field from a section to the root
        """
        from pyramid import testing
        from occams.forms import models, Session

        schema = models.Schema(
            name='testform',
            title=u'Test Form',
            attributes={
                'section1': models.Attribute(
                    name='section1',
                    title=u'Section 1',
                    type='section',
                    attributes={
                        'myvar': models.Attribute(
                            name='myvar',
                            title=u'My Var',
                            type='string',
                            order=1)
                        },
                    order=0)
                })
        Session.add(schema)
        Session.flush()

        request = testing.DummyRequest(json_body={
            'target': None,
            'index': 1
        })

        self._call_view(schema.attributes['myvar'], request)

        self.assertEqual(
            [(None, 'section1', 0), (None, 'myvar', 1)],
            self._comparable(schema))

    def test_from_section_to_section(self, check_csrf_token):
        """
        It should be able to move a field from a section to another
        """
        from pyramid import testing
        from occams.forms import models, Session

        schema = models.Schema(
            name='testform',
            title=u'Test Form',
            attributes={
                'section1': models.Attribute(
                    name='section1',
                    title=u'Section 1',
                    type='section',
                    attributes={
                        'myvar': models.Attribute(
                            name='myvar',
                            title=u'My Var',
                            type='string',
                            order=1)
                        },
                    order=0),
                'section2': models.Attribute(
                    name='section2',
                    title=u'Section 2',
                    type='section',
                    order=2)
                })
        Session.add(schema)
        Session.flush()

        request = testing.DummyRequest(json_body={
            'target': 'section2',
            'index': 0
        })

        self._call_view(schema.attributes['myvar'], request)

        self.assertEqual(
            [(None, 'section1', 0),
             (None, 'section2', 1),
             ('section2', 'myvar', 2)],
            self._comparable(schema))

    def test_from_within_section(self, check_csrf_token):
        """
        It should be able to move a field within a section
        """
        from pyramid import testing
        from occams.forms import models, Session

        schema = models.Schema(
            name='testform',
            title=u'Test Form',
            attributes={
                'section1': models.Attribute(
                    name='section1',
                    title=u'Section 1',
                    type='section',
                    attributes={
                        'myvar': models.Attribute(
                            name='myvar',
                            title=u'My Var',
                            type='string',
                            order=1),
                        'myfoo': models.Attribute(
                            name='myfoo',
                            title=u'My Foo',
                            type='string',
                            order=2)
                        },
                    order=0),
                })
        Session.add(schema)
        Session.flush()

        request = testing.DummyRequest(json_body={
            'target': 'section1',
            'index': 1
        })

        self._call_view(schema.attributes['myvar'], request)

        self.assertEqual(
            [(None, 'section1', 0),
             ('section1', 'myfoo', 1),
             ('section1', 'myvar', 2)],
            self._comparable(schema))
