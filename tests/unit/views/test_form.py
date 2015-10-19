class TestListJSON:

    def _call_fut(self, *args, **kw):
        from occams_forms.views.form import list_json
        return list_json(*args, **kw)

    def test_empty(self, req, db_session):
        """
        It should return an empty list if there are no schemata in the system
        """
        from occams_forms import models
        res = self._call_fut(models.FormFactory(req), req)
        assert res['forms'] == []

    def test_not_empty(self, req, db_session):
        """
        It should return a listing of schemata with links to each version
        """
        from datetime import date
        from occams_forms import models

        db_session.add(models.Schema(
            name=u'sample',
            title=u'Sample',
            publish_date=date(2014, 6, 1)
        ))
        db_session.flush()

        res = self._call_fut(models.FormFactory(req), req)

        assert 1 == len(res['forms'])

        record = res['forms'][0]
        assert 'sample' == record['name']
        assert False == record['has_private']
        assert 'Sample' == record['title']

        versions = record['versions']
        assert '2014-06-01' == versions[0]['publish_date']
