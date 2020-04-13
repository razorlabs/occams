class TestListJSON:

    def _call_fut(self, *args, **kw):
        from occams.views.form import list_json
        return list_json(*args, **kw)

    def test_empty(self, req, dbsession):
        """
        It should return an empty list if there are no schemata in the system
        """
        from occams import models
        res = self._call_fut(models.FormFactory(req), req)
        assert res['forms'] == []

    def test_not_empty(self, req, dbsession):
        """
        It should return a listing of schemata with links to each version
        """
        from datetime import date
        from occams import models

        dbsession.add(models.Schema(
            name='sample',
            title='Sample',
            publish_date=date(2014, 6, 1)
        ))
        dbsession.flush()

        res = self._call_fut(models.FormFactory(req), req)

        assert 1 == len(res['forms'])

        record = res['forms'][0]
        assert 'sample' == record['name']
        assert False == record['has_private']
        assert 'Sample' == record['title']

        versions = record['versions']
        assert '2014-06-01' == versions[0]['publish_date']
