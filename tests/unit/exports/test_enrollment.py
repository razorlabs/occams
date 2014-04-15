from tests import IntegrationFixture


class TestEnrollmentPlan(IntegrationFixture):

    def test_file_name(self):
        from occams.studies import exports
        plan = exports.EnrollmentPlan()
        self.assertEqual(plan.file_name, 'enrollment.csv')

    def test_columns(self):
        """
        It should generate a table of all the enrollments in the database
        """
        from occams.studies import exports
        plan = exports.EnrollmentPlan()

        codebook = list(plan.codebook())
        query = plan.data()

        codebook_columns = [c['field'] for c in codebook]
        data_columns = [c['name'] for c in query.column_descriptions]

        self.assertItemsEqual(codebook_columns, data_columns)
