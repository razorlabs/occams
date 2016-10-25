class TestVisitPlan:

    def _create_one(self, *args, **kw):
        from occams_studies.exports.visit import VisitPlan
        return VisitPlan(*args, **kw)

    def test_file_name(self, db_session):
        plan = self._create_one(db_session)
        assert plan.file_name == 'visit.csv'

    def test_columns(self, db_session):
        """
        It should generate a table of all the visits in the database
        """
        plan = self._create_one(db_session)

        codebook = list(plan.codebook())
        query = plan.data()

        codebook_columns = [c['field'] for c in codebook]
        data_columns = [c['name'] for c in query.column_descriptions]

        assert sorted(codebook_columns) == sorted(data_columns)
