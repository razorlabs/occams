from tests import IntegrationFixture


class TestListJSON(IntegrationFixture):

    def _callView(self, request):
        from occams.forms.views.form import list_json
        return list_json(request)

    def test_empty(self):
        """
        It should return an empty list if there are no schemata in the system
        """
        from pyramid import testing
        result = self._callView(testing.DummyRequest())
        self.assertEqual([], result['forms'])

    def test_not_empty(self):
        """
        It should return a listing of schemata with links to each version
        """
        from datetime import date
        from pyramid import testing
        from occams.forms import Session, models
        from tests import track_user

        self.config.add_route('version_view', '/versions/{version}')

        track_user('joe')
        Session.add(models.Schema(
            name=u'sample',
            title=u'Sample',
            publish_date=date(2014, 6, 1)
        ))
        Session.flush()

        result = self._callView(testing.DummyRequest())

        self.assertEqual(1, len(result['forms']))

        record = result['forms'][0]
        self.assertEqual('sample', record['name'])
        self.assertEqual(False, record['has_private'])
        self.assertEqual('Sample', record['title'])

        versions = record['versions']
        self.assertEqual('2014-06-01', versions[0]['publish_date'])
