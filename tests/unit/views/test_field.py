from tests import IntegrationFixture


class TestList(IntegrationFixture):

    def _getView(self):
        from occams.forms.views.field import list_
        return list_

    def test_not_found(self):
        """
        It should send 404 if the form for the fields does not exist.
        """
        from pyramid.httpexceptions import HTTPNotFound
        from pyramid import testing
        view = self._getView()
        with self.assertRaises(HTTPNotFound):
            view(testing.DummyRequest(
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
        view = self._getView()
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
                    order=0)},
            sections={
                'sec1': models.Section(
                    name=u'sec1',
                    title=u'Section 1',
                    order=0,
                    attributes={
                        'mysubfield': models.Attribute(
                            name=u'mysubfield',
                            title=u'My Sub Field',
                            type=u'string',
                            order=1)})}))
        Session.flush()
        response = view(testing.DummyRequest(
            matchdict={
                'form': 'myform',
                'version': '2014-07-01',
            }))
        self.assertIn('attributes', response)
        self.assertIn('sections', response)


class TestView(IntegrationFixture):

    def _getView(self):
        from occams.forms.views.field import view
        return view

    def test_not_found(self):
        """
        It should send 404 if the attribute/field does not exist
        """
        from pyramid.httpexceptions import HTTPNotFound
        from pyramid import testing
        view = self._getView()
        with self.assertRaises(HTTPNotFound):
            view(testing.DummyRequest(
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
        view = self._getView()
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
        response = view(testing.DummyRequest(
            matchdict={
                'form': 'myform',
                'version': '2014-07-01',
                'field': 'myfield'
            }))
        self.assertEqual('myfield', response['name'])


class TestAdd(IntegrationFixture):

    def _getView(self):
        from occams.forms.views.field import add
        return add

    def test_not_found(self):
        """
        It should send 404 if the attribute/field does not exist
        """
        from pyramid.httpexceptions import HTTPNotFound
        from pyramid import testing
        view = self._getView()
        with self.assertRaises(HTTPNotFound):
            view(testing.DummyRequest(
                matchdict={
                    'form': 'myform',
                    'version': '2014-07-01',
                    'field': 'idontexist'
                }))

    def test_forbidden(self):
        """
        It should only allow administrators to update published forms
        """
        import mock
        from datetime import date
        from pyramid import testing
        from pyramid.httpexceptions import HTTPForbidden
        from webob.multidict import MultiDict

        class DummySchema(object):
            pass

        schema = DummySchema()
        schema.publish_date = date.today()

        with mock.patch('occams.forms.views.field.get_schema', ret_val=schema):
            with self.assertRaises(HTTPForbidden):
                view = self._getView()
                view(testing.DummyRequest(
                    post=MultiDict(),
                    matchdict={
                        'form': 'myform',
                        'version': '2014-07-01',
                        'field': 'myfield',
                        'type': 'string'
                    }))
