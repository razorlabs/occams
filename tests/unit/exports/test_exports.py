class TestWriteData:

    def test_unicode(self, dbsession):
        """
        It should be able to export unicode strings
        """
        from contextlib import closing
        import io
        from sqlalchemy import literal_column, Integer, Unicode
        from occams import exports

        query = dbsession.query(
            literal_column(u"'420'", Integer).label('anumeric'),
            literal_column(u"'¿Qué pasa?'", Unicode).label('astring'),
            )

        with closing(io.StringIO()) as fp:
            exports.write_data(fp, query)
            fp.seek(0)
            rows = [r for r in exports.csv.reader(fp)]

        assert sorted(['anumeric', 'astring']) == sorted(rows[0])
        assert sorted(['420', '¿Qué pasa?']) == sorted(rows[1])


class TestDumpCodeBook:

    def test_header(self, dbsession):
        """
        It should have the standard codebook header.
        """
        from contextlib import closing
        import io
        from occams import exports

        with closing(io.StringIO()) as fp:
            exports.write_codebook(fp, [])
            fp.seek(0)
            fieldnames = exports.csv.DictReader(fp).fieldnames

        assert sorted(fieldnames) == sorted(exports.codebook.HEADER)
