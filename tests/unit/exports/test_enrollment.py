from tests import IntegrationFixture


class TestEnrollmentPlan(IntegrationFixture):

    def test_file_name(self):
        from occams.clinical import exports
        plan = exports.enrollment.EnrollmentPlan()
        self.assertEqual(plan.file_name, 'enrollment.csv')

    def test_data_without_refs(self):
        """
        It should generate a table of all the enrollments in the database
        """
        from datetime import date
        from occams.clinical import exports, models, Session
        from occams.clinical.security import track_user
        plan = exports.enrollment.EnrollmentPlan()

        track_user('joe')

        patient = models.Patient(
            pid=u'xxx-xxx',
            legacy_number=u'12345',
            site=models.Site(name=u'someplace', title=u'Some Place'),
            enrollments=[
                models.Enrollment(
                    consent_date=date.today(),
                    reference_number=u'76C000000',
                    study=models.Study(
                        name=u'some_study',
                        code=u'9XY',
                        consent_date=date.today(),
                        short_title=u'smstdy',
                        title=u'Some Study')
                )
            ])

        Session.add(patient)

        codebook = list(plan.codebook())
        query = plan.data()

        codebook_columns = [c['field'] for c in codebook]
        data_columns = [c['name'] for c in query.column_descriptions]

        self.assertItemsEqual(codebook_columns, data_columns)
