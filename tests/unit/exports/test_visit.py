from tests import IntegrationFixture


class TestVisitPlan(IntegrationFixture):

    def test_file_name(self):
        from occams_studies import exports
        plan = exports.VisitPlan()
        self.assertEqual(plan.file_name, 'visit.csv')

    def test_columns(self):
        """
        It should generate a table of all the visits in the database
        """
        from occams_studies import exports
        plan = exports.VisitPlan()

        codebook = list(plan.codebook())
        query = plan.data()

        codebook_columns = [c['field'] for c in codebook]
        data_columns = [c['name'] for c in query.column_descriptions]

        self.assertItemsEqual(codebook_columns, data_columns)
