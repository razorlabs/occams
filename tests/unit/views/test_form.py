from tests import IntegrationFixture


class TestListJSON(IntegrationFixture):

    def _getView(self):
        from occams.form.views.form import list_json
        return list_json

    def test_empty(self):
        """
        It should return an empty list if there are no schemata in the system
        """
        from pyramid import testing
        view = self._getView()
        result = view(testing.DummyRequest())
        self.assertEqual([], result)

    def test_not_empty(self):
        """
        It should return a listing of schemata with links to each version
        """
        from datetime import date
        from pyramid import testing
        from occams.form import Session, models
        from tests import track_user

        self.config.add_route('version_view', '/dummy/{form}/{version}')

        track_user('joe')
        Session.add(models.Schema(
            name=u'sample',
            title=u'Sample',
            publish_date=date(2014, 6, 1)
        ))
        Session.flush()

        view = self._getView()
        result = view(testing.DummyRequest())

        self.assertEqual(1, len(result))

        record = result[0]
        self.assertEqual('sample', record['name'])
        self.assertEqual(False, record['has_private'])
        self.assertEqual('Sample', record['title'])

        versions = record['versions']
        self.assertEqual('2014-06-01', versions[0]['publish_date'])
