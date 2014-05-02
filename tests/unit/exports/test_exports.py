# -*- coding: utf-8 -*-

from tests import IntegrationFixture


class TestListAll(IntegrationFixture):

    def test_no_schemata(self):
        from occams.studies import exports
        exportables = exports.list_all()
        self.assertItemsEqual(
            ['pid', 'enrollment', 'SpecimenAliquot', 'visit'],
            exportables.keys())


class TestWriteData(IntegrationFixture):

    def test_unicode(self):
        """
        It should be able to export unicode strings
        """
        from contextlib import closing
        import six
        from sqlalchemy import literal_column, Integer, Unicode
        from occams.studies import Session
        from occams.studies import exports

        query = Session.query(
            literal_column(u"'420'", Integer).label(u'anumeric'),
            literal_column(u"'¿Qué pasa?'", Unicode).label(u'astring'),
            )

        with closing(six.BytesIO()) as fp:
            exports.write_data(fp, query)
            fp.seek(0)
            rows = [r for r in exports.csv.reader(fp)]

        self.assertItemsEqual(['anumeric', 'astring'], rows[0])
        self.assertItemsEqual([u'420', u'¿Qué pasa?'], rows[1])


class TestDumpCodeBook(IntegrationFixture):

    def test_header(self):
        """
        It should have the standard codebook header.
        """
        from contextlib import closing
        import six
        from occams.studies import exports

        with closing(six.BytesIO()) as fp:
            exports.write_codebook(fp, [])
            fp.seek(0)
            fieldnames = exports.csv.DictReader(fp).fieldnames

        self.assertItemsEqual(fieldnames, exports.codebook.HEADER)
