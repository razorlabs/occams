from tests import IntegrationFixture


class TestListJSON(IntegrationFixture):

    def _call_view(self, context, request):
        from occams_forms.views.form import list_json
        return list_json(context, request)

    def test_empty(self):
        """
        It should return an empty list if there are no schemata in the system
        """
        from pyramid import testing
        from occams_forms import models
        request = testing.DummyRequest()
        result = self._call_view(models.FormFactory(request), request)
        self.assertEqual([], result['forms'])

    def test_not_empty(self):
        """
        It should return a listing of schemata with links to each version
        """
        from datetime import date
        from pyramid import testing
        from occams_forms import Session, models

        self.config.add_route('forms.version', '/versions/{version}')

        Session.add(models.Schema(
            name=u'sample',
            title=u'Sample',
            publish_date=date(2014, 6, 1)
        ))
        Session.flush()

        request = testing.DummyRequest()
        result = self._call_view(models.FormFactory(request), request)

        self.assertEqual(1, len(result['forms']))

        record = result['forms'][0]
        self.assertEqual('sample', record['name'])
        self.assertEqual(False, record['has_private'])
        self.assertEqual('Sample', record['title'])

        versions = record['versions']
        self.assertEqual('2014-06-01', versions[0]['publish_date'])
