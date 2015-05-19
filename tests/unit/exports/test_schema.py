from tests import IntegrationFixture


class TestSchemaPlan(IntegrationFixture):

    def test_list_not_include_private(self):
        """
        It should not include private data if specified.
        Note this is not the same as de-identification)
        """
        from datetime import date
        from occams_studies import Session, models, exports

        schema = models.Schema(
            name=u'contact',
            title=u'Contact Details',
            publish_date=date.today(),
            attributes={
                'foo': models.Attribute(
                    name='foo',
                    title=u'',
                    type='string',
                    order=0,
                    is_private=True
                )})

        Session.add_all([schema])
        Session.flush()

        plans = exports.SchemaPlan.list_all(include_private=True)
        self.assertEqual(len(plans), 1)

        plans = exports.SchemaPlan.list_all(include_private=False)
        self.assertEqual(len(plans), 0)

    def test_list_not_include_rand(self):
        """
        It should not include randomization data if specified.
        """
        from datetime import date, timedelta
        from occams_studies import Session, models, exports

        schema = models.Schema(
            name=u'vitals',
            title=u'Vitals',
            publish_date=date.today(),
            attributes={
                'foo': models.Attribute(
                    name='foo',
                    title=u'',
                    type='string',
                    order=0,
                )})
        entity = models.Entity(
            collect_date=date.today(),
            schema=schema)
        study = models.Study(
            name=u'study1',
            short_title=u'S1',
            code=u'001',
            consent_date=date.today() - timedelta(365),
            title=u'Study 1')
        armga = models.Arm(
            name=u'groupa',
            title=u'GROUP A',
            study=study)
        stratum = models.Stratum(
            study=study,
            arm=armga,
            block_number=12384,
            randid=u'8484',
            entities=[entity])
        Session.add_all([schema, entity, stratum])
        Session.flush()

        plans = exports.SchemaPlan.list_all(include_rand=True)
        self.assertEqual(len(plans), 1)

        plans = exports.SchemaPlan.list_all(include_rand=False)
        self.assertEqual(len(plans), 0)

    def test_patient(self):
        """
        It should add patient-specific metadata to the report
        """
        from datetime import date
        from occams_studies import Session, models, exports

        schema = models.Schema(
            name=u'contact',
            title=u'Contact Details',
            publish_date=date.today(),
            attributes={
                'foo': models.Attribute(
                    name='foo',
                    title=u'',
                    type='string',
                    order=0,
                )})
        entity = models.Entity(
            schema=schema,
            collect_date=date.today())
        patient = models.Patient(
            site=models.Site(name='ucsd', title=u'UCSD'),
            pid=u'12345',
            entities=[entity])
        Session.add_all([schema, entity, patient])
        Session.flush()

        plan = exports.SchemaPlan.from_schema(name=schema.name)
        codebook = list(plan.codebook())
        query = plan.data()
        codebook_columns = [c['field'] for c in codebook]
        data_columns = [c['name'] for c in query.column_descriptions]
        record = query.one()
        self.assertItemsEqual(codebook_columns, data_columns)
        self.assertEquals(record.site, patient.site.name)
        self.assertEquals(record.pid, patient.pid)
        self.assertIsNone(record.enrollment)
        self.assertIsNone(record.visit_cycles)
        self.assertIsNone(record.visit_date)
        self.assertEquals(record.collect_date, entity.collect_date)

    def test_enrollment(self):
        """
        It should add enrollment-specific metadata to the report
        """
        from datetime import date, timedelta
        from occams_studies import Session, models, exports

        schema = models.Schema(
            name=u'termination',
            title=u'Termination',
            publish_date=date.today(),
            attributes={
                'foo': models.Attribute(
                    name='foo',
                    title=u'',
                    type='string',
                    order=0,
                )})
        entity = models.Entity(
            schema=schema,
            collect_date=date.today())
        patient = models.Patient(
            site=models.Site(name='ucsd', title=u'UCSD'),
            pid=u'12345',
            entities=[entity])
        study = models.Study(
            name=u'cooties',
            short_title=u'CTY',
            code=u'999',
            consent_date=date.today() - timedelta(365),
            title=u'Cooties')
        enrollment = models.Enrollment(
            patient=patient,
            study=study,
            consent_date=date.today() - timedelta(5),
            latest_consent_date=date.today() - timedelta(3),
            termination_date=date.today(),
            entities=[entity])
        Session.add_all([schema, entity, patient, study, enrollment])

        plan = exports.SchemaPlan.from_schema(name=schema.name)
        codebook = list(plan.codebook())
        query = plan.data()
        codebook_columns = [c['field'] for c in codebook]
        data_columns = [c['name'] for c in query.column_descriptions]
        record = query.one()
        self.assertItemsEqual(codebook_columns, data_columns)
        self.assertEquals(record.site, patient.site.name)
        self.assertEquals(record.pid, patient.pid)
        self.assertEquals(record.enrollment, enrollment.study.name)
        self.assertEquals(record.enrollment_ids, str(enrollment.id))
        self.assertIsNone(record.visit_cycles)
        self.assertEquals(record.collect_date, entity.collect_date)

    def test_visit(self):
        """
        It should add visit-specific metadata to the report
        """
        from datetime import date, timedelta
        from occams_studies import Session, models, exports

        schema = models.Schema(
            name=u'vitals',
            title=u'Vitals',
            publish_date=date.today(),
            attributes={
                'foo': models.Attribute(
                    name='foo',
                    title=u'',
                    type='string',
                    order=0,
                )})
        entity = models.Entity(
            collect_date=date.today(),
            schema=schema)
        patient = models.Patient(
            site=models.Site(name='ucsd', title=u'UCSD'),
            pid=u'12345',
            entities=[entity])
        visit = models.Visit(
            visit_date=date.today(),
            patient=patient,
            cycles=[
                models.Cycle(
                    name=u'study1-scr',
                    title=u'Study 1 Screening',
                    week=123,
                    study=models.Study(
                        name=u'study1',
                        short_title=u'S1',
                        code=u'001',
                        consent_date=date.today() - timedelta(365),
                        title=u'Study 1')),
                models.Cycle(
                    name=u'study2-wk1',
                    title=u'Study 2 Week 1',
                    week=5858,
                    study=models.Study(
                        name=u'study21',
                        short_title=u'S2',
                        code=u'002',
                        consent_date=date.today() - timedelta(365),
                        title=u'Study 2'))],
            entities=[entity])
        Session.add_all([schema, entity, patient, visit])
        Session.flush()

        plan = exports.SchemaPlan.from_schema(name=schema.name)
        codebook = list(plan.codebook())
        query = plan.data()
        codebook_columns = [c['field'] for c in codebook]
        data_columns = [c['name'] for c in query.column_descriptions]
        record = query.one()
        self.assertItemsEqual(codebook_columns, data_columns)
        self.assertEquals(record.site, patient.site.name)
        self.assertEquals(record.pid, patient.pid)
        self.assertIsNone(record.enrollment)
        cyclefmt = '{cycle.study.title}({cycle.week})'
        self.assertItemsEqual(
            record.visit_cycles.split(';'),
            [cyclefmt.format(cycle=c) for c in visit.cycles])
        self.assertEquals(str(record.visit_id), str(visit.id))
        self.assertEquals(record.collect_date, entity.collect_date)

    def test_rand(self):
        """
        It should add randomization-specific metadata to the report
        """
        from datetime import date, timedelta
        from occams_studies import Session, models, exports

        schema = models.Schema(
            name=u'vitals',
            title=u'Vitals',
            publish_date=date.today(),
            attributes={
                'foo': models.Attribute(
                    name='foo',
                    title=u'',
                    type='string',
                    order=0,
                )})
        entity = models.Entity(
            collect_date=date.today(),
            schema=schema)
        patient = models.Patient(
            site=models.Site(name='ucsd', title=u'UCSD'),
            pid=u'12345',
            entities=[entity])
        study = models.Study(
            name=u'study1',
            short_title=u'S1',
            code=u'001',
            consent_date=date.today() - timedelta(365),
            title=u'Study 1')
        armga = models.Arm(
            name=u'groupa',
            title=u'GROUP A',
            study=study)
        stratum = models.Stratum(
            study=study,
            arm=armga,
            block_number=12384,
            randid=u'8484',
            patient=patient,
            entities=[entity])
        enrollment = models.Enrollment(
            patient=patient,
            study=study,
            consent_date=date.today() - timedelta(5),
            latest_consent_date=date.today() - timedelta(3),
            termination_date=date.today(),
            entities=[entity])
        Session.add_all([schema, entity, patient, enrollment, stratum])
        Session.flush()

        plan = exports.SchemaPlan.from_schema(name=schema.name)
        codebook = list(plan.codebook())
        query = plan.data()
        codebook_columns = [c['field'] for c in codebook]
        data_columns = [c['name'] for c in query.column_descriptions]
        record = query.one()
        self.assertItemsEqual(codebook_columns, data_columns)
        self.assertEquals(record.site, patient.site.name)
        self.assertEquals(record.pid, patient.pid)
        self.assertEquals(record.enrollment, enrollment.study.name)
        self.assertEquals(record.enrollment_ids, str(enrollment.id))
        self.assertEquals(record.collect_date, entity.collect_date)
        self.assertEquals(record.block_number, stratum.block_number)
        self.assertEquals(record.arm_name, stratum.arm.title)
        self.assertEquals(record.randid, stratum.randid)
