from tests import IntegrationFixture


class TestListJSON(IntegrationFixture):

    def _callView(self, request):
        from occams.forms.views.field import list_json
        return list_json(request)

    def test_not_found(self):
        """
        It should send 404 if the form for the fields does not exist.
        """
        from pyramid.httpexceptions import HTTPNotFound
        from pyramid import testing
        with self.assertRaises(HTTPNotFound):
            self._callView(testing.DummyRequest(
                matchdict={
                    'form': 'idontexist',
                    'version': '2014-07-01',
                }))

    def test_basic(self):
        """
        It should return a listing of a form's attributes and sections
        """
        from datetime import date
        from pyramid import testing
        from occams.forms import Session, models
        from tests import track_user
        self.config.add_route('field_list', '/fields')
        self.config.add_route('field_view', '/field/{field}')
        track_user('joe')
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
        response = self._callView(testing.DummyRequest(
            matchdict={
                'form': 'myform',
                'version': '2014-07-01',
            }))
        self.assertIn('fields', response)


class TestViewJSON(IntegrationFixture):

    def _callView(self, request):
        from occams.forms.views.field import view_json
        return view_json(request)

    def test_not_found(self):
        """
        It should send 404 if the attribute/field does not exist
        """
        from pyramid.httpexceptions import HTTPNotFound
        from pyramid import testing
        with self.assertRaises(HTTPNotFound):
            self._callView(testing.DummyRequest(
                matchdict={
                    'form': 'myform',
                    'version': '2014-07-01',
                    'field': 'idontexist'
                }))

    def test_basic(self):
        """
        It should return the attribute's properties in JSON form
        """
        from datetime import date
        from pyramid import testing
        from occams.forms import Session, models
        from tests import track_user
        self.config.add_route('field_view', '/field/{field}')
        track_user('joe')
        Session.add(models.Schema(
            name=u'myform',
            title=u'My Form',
            publish_date=date(2014, 7, 1),
            attributes={
                'myfield': models.Attribute(
                    name=u'myfield',
                    title=u'My Field',
                    type=u'string',
                    order=0)}))
        Session.flush()
        response = self._callView(testing.DummyRequest(
            matchdict={
                'form': 'myform',
                'version': '2014-07-01',
                'field': 'myfield'
            }))
        self.assertEqual('myfield', response['name'])


class TestAddJSON(IntegrationFixture):

    def _callView(self, request):
        from occams.forms.views.field import add_json
        return add_json(request)

    def test_not_found(self):
        """
        It should send 404 if the attribute/field does not exist
        """
        from pyramid.httpexceptions import HTTPNotFound
        from pyramid import testing
        with self.assertRaises(HTTPNotFound):
            self._callView(testing.DummyRequest(
                matchdict={
                    'form': 'myform',
                    'version': '2014-07-01',
                    'field': 'idontexist'
                }))

    def test_forbidden(self):
        """
        It should only allow priviledged users to update published forms
        """
        from datetime import date
        from pyramid import testing
        from pyramid.httpexceptions import HTTPForbidden
        from occams.forms import models, Session
        from tests import track_user

        track_user('joe')
        schema = models.Schema(
            name=u'myform',
            title=u'',
            publish_date=date(2014, 7, 1))
        Session.add(schema)
        Session.flush()

        self.config.testing_securitypolicy(permissive=False)

        with self.assertRaises(HTTPForbidden):
            self._callView(testing.DummyRequest(
                matchdict={
                    'form': schema.name,
                    'version': str(schema.publish_date),
                }))


def TestMoveJSON(IntegrationFixture):

    def _callView(self, request):
        from occams.forms.views.field import move_json
        return move_json(request)

    def test_not_found(self):
        """
        It should send 404 if the attribute/field does not exist
        """
        from pyramid.httpexceptions import HTTPNotFound
        from pyramid import testing
        with self.assertRaises(HTTPNotFound):
            self._callView(testing.DummyRequest(
                matchdict={
                    'form': 'myform',
                    'version': '2014-07-01',
                    'field': 'idontexist'
                }))

    def test_forbidden(self):
        """
        It should only allow priviledged users to update published forms
        """
        from datetime import date
        from pyramid import testing
        from pyramid.httpexceptions import HTTPForbidden
        from occams.forms import models, Session
        from tests import track_user

        track_user('joe')
        schema = models.Schema(
            name=u'myform',
            title=u'',
            publish_date=date(2014, 7, 1))
        Session.add(schema)
        Session.flush()

        self.config.testing_securitypolicy(permissive=False)

        with self.assertRaises(HTTPForbidden):
            self._callView(testing.DummyRequest(
                matchdict={
                    'form': schema.name,
                    'version': str(schema.publish_date),
                }))


class TestMoveField(IntegrationFixture):

    def test_no_nested_section(self):
        """
        It should not allow nested sections
        """
        from pyramid.httpexceptions import HTTPBadRequest
        from occams.forms import models
        from occams.forms.views.field import move_field

        schema = models.Schema(
            name=u'myform',
            title=u'',
            attributes={
                's': models.Attribute(
                    name=u's', title=u'', type='section', order=0),
                't': models.Attribute(
                    name=u't', title=u'', type='section', order=1)})

        with self.assertRaises(HTTPBadRequest):
            move_field(schema,
                       schema.attributes['t'],
                       into=schema.attributes['s'])

    def test_move_inside(self):
        """
        It should be able to move a field within the set
        """
        from occams.forms import models
        from occams.forms.views.field import move_field

        schema = models.Schema(
            name=u'myform',
            title=u'',
            attributes={
                's': models.Attribute(
                    name=u's', title=u'', type='section', order=0,
                    attributes={
                        'a': models.Attribute(
                            name=u'a', title=u'', type='string', order=1),
                        'b': models.Attribute(
                            name=u'b', title=u'', type='string', order=2),
                        'c': models.Attribute(
                            name=u'c', title=u'', type='string', order=3),
                        'd': models.Attribute(
                            name=u'd', title=u'', type='string', order=4)})})

        move_field(schema,
                   schema.attributes['d'],
                   into=schema.attributes['s'],
                   after=schema.attributes['b'])

        # The new order
        self.assertEquals(schema.attributes['a'].order, 1)
        self.assertEquals(schema.attributes['b'].order, 2)
        self.assertEquals(schema.attributes['d'].order, 3)
        self.assertEquals(schema.attributes['c'].order, 4)

    def test_move_front(self):
        """
        It should be able to move to the front of the set
        """
        from occams.forms import models
        from occams.forms.views.field import move_field

        schema = models.Schema(
            name=u'myform',
            title=u'',
            attributes={
                's': models.Attribute(
                    name=u's', title=u'', type='section', order=0,
                    attributes={
                        'a': models.Attribute(
                            name=u'a', title=u'', type='string', order=1),
                        'b': models.Attribute(
                            name=u'b', title=u'', type='string', order=2),
                        'c': models.Attribute(
                            name=u'c', title=u'', type='string', order=3),
                        'd': models.Attribute(
                            name=u'd', title=u'', type='string', order=4)})})

        move_field(schema, schema.attributes['d'],
                   into=schema.attributes['s'], after=None)

        # The new order
        self.assertEquals(schema.attributes['d'].order, 1)
        self.assertEquals(schema.attributes['a'].order, 2)
        self.assertEquals(schema.attributes['b'].order, 3)
        self.assertEquals(schema.attributes['c'].order, 4)

    def test_move_into_section(self):
        """
        It should be able to move into a section
        """
        from occams.forms import models
        from occams.forms.views.field import move_field

        schema = models.Schema(
            name=u'myform',
            title=u'',
            attributes={
                'x': models.Attribute(
                    name=u'x', title=u'', type='string', order=0),
                's': models.Attribute(
                    name=u's', title=u'', type='section', order=1,
                    attributes={
                        'a': models.Attribute(
                            name=u'a', title=u'', type='string', order=2),
                        'b': models.Attribute(
                            name=u'b', title=u'', type='string', order=3),
                        'c': models.Attribute(
                            name=u'c', title=u'', type='string', order=4),
                        'd': models.Attribute(
                            name=u'd', title=u'', type='string', order=5)})})

        move_field(schema, schema.attributes['x'],
                   into=schema.attributes['s'],
                   after=schema.attributes['b'])

        # The new order
        self.assertEquals(schema.attributes['s'].order, 0)
        self.assertEquals(schema.attributes['a'].order, 1)
        self.assertEquals(schema.attributes['b'].order, 2)
        self.assertEquals(schema.attributes['x'].order, 3)
        self.assertEquals(schema.attributes['c'].order, 4)
        self.assertEquals(schema.attributes['d'].order, 5)
        self.assertIn('x', schema.attributes['s'].attributes)

    def test_move_from_section(self):
        """
        It should be able to move out from a section
        """
        from occams.forms import models
        from occams.forms.views.field import move_field

        schema = models.Schema(
            name=u'myform',
            title=u'',
            attributes={
                's': models.Attribute(
                    name=u's', title=u'', type='section', order=0,
                    attributes={
                        'a': models.Attribute(
                            name=u'a', title=u'', type='string', order=1),
                        'b': models.Attribute(
                            name=u'b', title=u'', type='string', order=2),
                        'c': models.Attribute(
                            name=u'c', title=u'', type='string', order=3),
                        'd': models.Attribute(
                            name=u'd', title=u'', type='string', order=4)})})

        move_field(schema, schema.attributes['c'],
                   into=None,
                   after=schema.attributes['s'])

        # The new order
        self.assertEquals(schema.attributes['s'].order, 0)
        self.assertEquals(schema.attributes['a'].order, 1)
        self.assertEquals(schema.attributes['b'].order, 2)
        self.assertEquals(schema.attributes['d'].order, 3)
        self.assertEquals(schema.attributes['c'].order, 4)
        self.assertNotIn('c', schema.attributes['s'].attributes)
