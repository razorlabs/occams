import pytest


class TestPidPlan:

    def test_file_name(self, db_session):
        from occams_studies import exports
        plan = exports.PidPlan(db_session)
        assert plan.file_name == 'pid.csv'

    def test_columns(self, db_session):
        """
        It should generate a table of all the pids in the database
        """

        from occams_studies import exports
        plan = exports.PidPlan(db_session)

        codebook = list(plan.codebook())
        query = plan.data()

        codebook_columns = [c['field'] for c in codebook]
        data_columns = [c['name'] for c in query.column_descriptions]

        assert sorted(codebook_columns) == sorted(data_columns)

    def test_data_without_refs(self, db_session):
        """
        It should be able to generate reports without refs
        """
        from occams_studies import exports, models
        plan = exports.PidPlan(db_session)

        patient = models.Patient(
            pid=u'xxx-xxx',
            site=models.Site(name=u'someplace', title=u'Some Place')
        )

        db_session.add(patient)

        codebook = list(plan.codebook())
        query = plan.data()

        codebook_columns = [c['field'] for c in codebook]
        data_columns = [c['name'] for c in query.column_descriptions]

        assert sorted(codebook_columns) == sorted(data_columns)

        data = query.one()._asdict()
        assert data['pid'] == patient.pid
        assert data['site'] == patient.site.name
        assert data['early_id'] is None

    def test_data_with_refs(self, db_session):
        """
        It should generate a basic listing of all the PIDs in the database
        """
        from occams_studies import exports, models
        plan = exports.PidPlan(db_session)

        reference_type = models.ReferenceType(
            name=u'med_num', title=u'Medical Number')

        patient = models.Patient(
            pid=u'xxx-xxx',
            references=[
                models.PatientReference(
                    reference_type=reference_type,
                    reference_number=u'999')
                ],
            site=models.Site(name=u'someplace', title=u'Some Place')
        )

        db_session.add(patient)

        codebook = list(plan.codebook())
        query = plan.data()

        codebook_columns = [c['field'] for c in codebook]
        data_columns = [c['name'] for c in query.column_descriptions]
        assert sorted(codebook_columns) == sorted(data_columns)

        data = query.one()._asdict()
        assert data['med_num'] == '999'

    @pytest.mark.parametrize('study_code', [u'ET', u'LTW', u'CVCT'])
    def test_data_with_early_test(self, db_session, study_code):
        """
        It should output earlytest ids (for backwards-compatibilty)
        """
        from datetime import date
        from occams_studies import exports, models
        plan = exports.PidPlan(db_session)

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

        db_session.add(patient)

        query = plan.data()
        data = query.one()._asdict()
        assert data['early_id'] == patient.enrollments[0].reference_number
