# -*- coding: utf-8 -*-


class TestListAll:

    def test_list(self, db_session):
        from occams_studies import exports
        from occams_studies.exports.plan import ExportPlan

        class SomePlan(ExportPlan):
            name = 'someplan'
            title = u'Some Plan'

        plans = [SomePlan]
        exportables = exports.list_all(plans, db_session)
        assert sorted(['someplan']) == sorted(exportables.keys())


class TestWriteData:

    def test_unicode(self, db_session):
        """
        It should be able to export unicode strings
        """
        from contextlib import closing
        import six
        from sqlalchemy import literal_column, Integer, Unicode
        from occams_studies import exports

        query = db_session.query(
            literal_column(u"'420'", Integer).label(u'anumeric'),
            literal_column(u"'¿Qué pasa?'", Unicode).label(u'astring'),
            )

        with closing(six.BytesIO()) as fp:
            exports.write_data(fp, query)
            fp.seek(0)
            rows = [r for r in exports.csv.reader(fp)]

        assert sorted(['anumeric', 'astring']) == sorted(rows[0])
        assert sorted([u'420', u'¿Qué pasa?']) == sorted(rows[1])


class TestDumpCodeBook:

    def test_header(self, db_session):
        """
        It should have the standard codebook header.
        """
        from contextlib import closing
        import six
        from occams_studies import exports

        with closing(six.BytesIO()) as fp:
            exports.write_codebook(fp, [])
            fp.seek(0)
            fieldnames = exports.csv.DictReader(fp).fieldnames

        assert sorted(fieldnames) == sorted(exports.codebook.HEADER)
