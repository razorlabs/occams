class TestVisitPlan:

    def _create_one(self, *args, **kw):
        from occams.exports.visit import VisitPlan
        return VisitPlan(*args, **kw)

    def test_file_name(self, dbsession):
        plan = self._create_one(dbsession)
        assert plan.file_name == 'visit.csv'

    def test_columns(self, dbsession):
        """
        It should generate a table of all the visits in the database
        """
        plan = self._create_one(dbsession)

        codebook = list(plan.codebook())
        query = plan.data()

        codebook_columns = [c['field'] for c in codebook]
        data_columns = [c['name'] for c in query.column_descriptions]

        assert sorted(codebook_columns) == sorted(data_columns)
