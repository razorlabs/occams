
class TestAvailableReferenceTypes:

    def _call_fut(self, *args, **kw):
        from occams_studies.views.reference_type \
            import available_reference_types as view
        return view(*args, **kw)

    def test_no_match(self, req, db_session):

        from occams_studies import models

        reftype = models.ReferenceType(
            name=u'medical_number',
            title=u'Medical Number'
        )

        db_session.add(reftype)

        req.GET = {'term': 'other'}
        factory = models.ReferenceTypeFactory(req)

        res = self._call_fut(factory, req)

        assert len(res['reference_types']) == 0, \
            'Reference types were found when none were expected'

    def test_match(self, req, db_session):

        from occams_studies import models

        reftype = models.ReferenceType(
            name=u'medical_number',
            title=u'Medical Number'
        )

        db_session.add(reftype)

        req.GET = {'term': 'med'}
        factory = models.ReferenceTypeFactory(req)

        res = self._call_fut(factory, req)

        assert len(res['reference_types']) == 1, \
            'Incorrect number of results received'
