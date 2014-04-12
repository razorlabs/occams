from tests import IntegrationFixture


class TestLabPlan(IntegrationFixture):

    def test_file_name(self):
        from occams.clinical import exports
        plan = exports.LabPlan()
        self.assertEqual(plan.file_name, 'SpecimenAliquot.csv')

    def test_columns(self):
        """
        It should generate a table of all the enrollments in the database
        """
        from occams.clinical import exports
        plan = exports.LabPlan()

        codebook = list(plan.codebook())
        query = plan.data()

        codebook_columns = [c['field'] for c in codebook]
        data_columns = [c['name'] for c in query.column_descriptions]

        self.assertItemsEqual(codebook_columns, data_columns)
