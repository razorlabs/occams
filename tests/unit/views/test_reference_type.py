from tests import IntegrationFixture


def _register_routes(config):
    config.add_route('studies.reference_type', '/r/{reference_type}')


class TestAvailableReferenceTypes(IntegrationFixture):

    def call_view(self, context, request):
        from occams_studies.views.reference_type \
            import available_reference_types as view
        return view(context, request)

    def test_no_match(self):

        from pyramid import testing
        from occams_studies import models, Session

        _register_routes(self.config)

        reftype = models.ReferenceType(
            name=u'medical_number',
            title=u'Medical Number'
        )

        Session.add(reftype)

        request = testing.DummyRequest(params={'term': 'other'})
        factory = models.ReferenceTypeFactory(request)

        response = self.call_view(factory, request)

        self.assertEquals(
            0, len(response['reference_types']),
            'Reference types were found when none were expected')

    def test_match(self):

        from pyramid import testing
        from occams_studies import models, Session

        _register_routes(self.config)

        reftype = models.ReferenceType(
            name=u'medical_number',
            title=u'Medical Number'
        )

        Session.add(reftype)

        request = testing.DummyRequest(params={'term': 'med'})
        factory = models.ReferenceTypeFactory(request)

        response = self.call_view(factory, request)

        self.assertEquals(
            1, len(response['reference_types']),
            'Incorrect number of results received')
