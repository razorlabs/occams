import mock

from tests import IntegrationFixture


class TestViewJSON(IntegrationFixture):

    def call_view(self, context, request):
        from occams_studies.views.form import view_json as view
        return view(context, request)

    def test_with_state(self):
        """
        It should generate state data is available
        """
        from pyramid import testing
        from occams_studies import models, Session
        from datetime import date

        myfirst = models.Schema(
            name=u'myfirst',
            title=u'My First Schema',
            publish_date=date.today()
        )
        default_state = models.State(
            name='pending-entry', title=u'Pending Entry')
        mydata = models.Entity(schema=myfirst, state=default_state)
        Session.add(mydata)
        Session.flush()
        mydata.__parent__ = mock.MagicMock()
        mydata.__parent__.__parent__ = mock.MagicMock()

        # import nose; nose.tools.set_trace()

        request = testing.DummyRequest()
        request.session.changed = mock.Mock()
        response = self.call_view(mydata, request)

        self.assertIsNotNone(response['state'])

    def test_without_state(self):
        """
        It should generate none if no state data is available
        """
        from pyramid import testing
        from occams_studies import models, Session
        from datetime import date

        myfirst = models.Schema(
            name=u'myfirst',
            title=u'My First Schema',
            publish_date=date.today()
        )
        mydata = models.Entity(schema=myfirst)
        Session.add(mydata)
        Session.flush()
        mydata.__parent__ = mock.MagicMock()
        mydata.__parent__.__parent__ = mock.MagicMock()

        # import nose; nose.tools.set_trace()

        request = testing.DummyRequest()
        request.session.changed = mock.Mock()
        response = self.call_view(mydata, request)

        self.assertIsNone(response['state'])
