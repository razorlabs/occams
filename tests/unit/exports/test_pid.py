from ddt import ddt, data
from tests import IntegrationFixture


@ddt
class TestPidPlan(IntegrationFixture):

    def test_file_name(self):
        from occams.clinical import exports
        plan = exports.PidPlan()
        self.assertEqual(plan.file_name, 'pid.csv')

    def test_columns(self):
        """
        It should generate a table of all the pids in the database
        """

        from occams.clinical import exports
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
        from occams.clinical import exports, models, Session
        from occams.clinical.security import track_user
        plan = exports.PidPlan()

        track_user('joe')

        patient = models.Patient(
            pid=u'xxx-xxx',
            legacy_number=u'12345',
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
        self.assertEqual(data['aeh_num'], patient.legacy_number)

    def test_data_with_refs(self):
        """
        It should generate a basic listing of all the PIDs in the database
        """
        from occams.clinical import exports, models, Session
        from occams.clinical.security import track_user
        plan = exports.PidPlan()

        track_user('joe')

        reftype = models.RefType(name=u'med_num', title=u'Medical Number')

        patient = models.Patient(
            pid=u'xxx-xxx',
            legacy_number=u'12345',
            reference_numbers=[
                models.PatientReference(
                    reftype=reftype,
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
        from occams.clinical import exports, models, Session
        from occams.clinical.security import track_user
        plan = exports.PidPlan()

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
