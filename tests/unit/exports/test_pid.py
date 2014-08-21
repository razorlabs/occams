from ddt import ddt, data
from tests import IntegrationFixture


@ddt
class TestPidPlan(IntegrationFixture):

    def test_file_name(self):
        from occams.studies import exports
        plan = exports.PidPlan()
        self.assertEqual(plan.file_name, 'pid.csv')

    def test_columns(self):
        """
        It should generate a table of all the pids in the database
        """

        from occams.studies import exports
        plan = exports.PidPlan()

        codebook = list(plan.codebook())
        query = plan.data()

        codebook_columns = [c['field'] for c in codebook]
        data_columns = [c['name'] for c in query.column_descriptions]

        self.assertItemsEqual(codebook_columns, data_columns)

    def test_data_without_refs(self):
        """
        It should be able to generate reports without refs
        """
        from occams.studies import exports, models, Session
        plan = exports.PidPlan()

        patient = models.Patient(
            pid=u'xxx-xxx',
            site=models.Site(name=u'someplace', title=u'Some Place')
        )

        Session.add(patient)

        codebook = list(plan.codebook())
        query = plan.data()

        codebook_columns = [c['field'] for c in codebook]
        data_columns = [c['name'] for c in query.column_descriptions]

        self.assertItemsEqual(codebook_columns, data_columns)

        data = query.one()._asdict()
        self.assertEqual(data['pid'], patient.pid)
        self.assertEqual(data['site'], patient.site.name)
        self.assertIsNone(data['early_id'])

    def test_data_with_refs(self):
        """
        It should generate a basic listing of all the PIDs in the database
        """
        from occams.studies import exports, models, Session
        plan = exports.PidPlan()

        reference_type = models.ReferenceType(name=u'med_num', title=u'Medical Number')

        patient = models.Patient(
            pid=u'xxx-xxx',
            references=[
                models.PatientReference(
                    reference_type=reference_type,
                    reference_number=u'999')
                ],
            site=models.Site(name=u'someplace', title=u'Some Place')
        )

        Session.add(patient)

        codebook = list(plan.codebook())
        query = plan.data()

        codebook_columns = [c['field'] for c in codebook]
        data_columns = [c['name'] for c in query.column_descriptions]
        self.assertItemsEqual(codebook_columns, data_columns)

        data = query.one()._asdict()
        self.assertEqual(data['med_num'], '999')

    @data(u'ET', u'LTW', u'CVCT')
    def test_data_with_early_test(self, study_code):
        """
        It should output earlytest ids (for backwards-compatibilty)
        """
        from datetime import date
        from occams.studies import exports, models, Session
        plan = exports.PidPlan()

        patient = models.Patient(
            pid=u'xxx-xxx',
            site=models.Site(name=u'someplace', title=u'Some Place'),
            enrollments=[
                models.Enrollment(
                    consent_date=date.today(),
                    reference_number=u'76C000000',
                    study=models.Study(
                        name=u'some_study',
                        code=study_code,
                        consent_date=date.today(),
                        short_title=u'smstdy',
                        title=u'Some Study')
                )
            ])

        Session.add(patient)

        query = plan.data()
        data = query.one()._asdict()
        self.assertEqual(
            data['early_id'],
            patient.enrollments[0].reference_number)
