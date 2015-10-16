class TestLabPlan:
    # don't test columns, this breaks the rest of the unit tests...
    # wait until this data file is moved to occams.lab

    def test_file_name(self, db_session):
        from occams_studies import exports
        plan = exports.LabPlan(db_session)
        assert plan.file_name == 'SpecimenAliquot.csv'
