from ddt import ddt, data

from tests import FunctionalFixture, USERID

@ddt
class TestPermissionsEnrollmentsListView(FunctionalFixture):

    url = '/studies/patients/123/enrollments'

    def setUp(self):
        super(TestPermissionsEnrollmentsListView, self).setUp()

        import transaction
        from occams import Session
        from occams_studies import models as studies
        from occams_datastore import models as datastore
        from datetime import date

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            Session.info['blame'] = user
            Session.add(user)
            Session.flush()
            site = studies.Site(
                name=u'UCSD',
                title=u'UCSD',
                description=u'UCSD Campus',
                create_date=date.today())

            patient = studies.Patient(
                initials=u'ian',
                nurse=u'imanurse@ucsd.edu',
                site=site,
                pid=u'123'
            )

            form = datastore.Schema(
                name=u'test_schema',
                title=u'test_title',
                publish_date=date(2015, 1, 1)
            )

            study = studies.Study(
                name=u'test_study',
                code=u'test_code',
                consent_date=date(2014, 12, 23),
                is_randomized=False,
                title=u'test_title',
                short_title=u'test_short',
                start_date=date(2014, 12, 12),
                schemata=set([form])
            )

            Session.add(studies.State(
                name=u'pending-entry',
                title=u'pending-entry'
            ))

            Session.add(studies.Enrollment(
                patient=patient,
                study=study,
                consent_date=date(2014, 12, 22)
            ))

    @data('administrator', 'manager', 'UCSD:enterer', 'UCSD:reviewer', 'UCSD:consumer', 'UCSD:member')
    def test_allowed(self, group):
        from occams import Session

        environ = self.make_environ(userid=USERID, groups=[group])

        response = self.app.get(
            self.url,
            extra_environ=environ,
            status='*',
            xhr=True,
            params={})

        self.assertEquals(200, response.status_code)

    def test_not_authenticated(self):
        self.app.get(self.url, status=401, xhr=True)
