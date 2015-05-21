from ddt import ddt, data

from tests import FunctionalFixture, USERID


@ddt
class TestPermissionForms(FunctionalFixture):
    def setUp(self):
        super(TestPermissionForms, self).setUp()

        from datetime import date

        import transaction
        from occams import Session
        from occams_studies import models as forms
        from occams_datastore import models as datastore

        # Any view-dependent data goes here
        # Webtests will use a different scope for its transaction
        with transaction.manager:
            user = datastore.User(key=USERID)
            Session.info['blame'] = user
            Session.add(user)
            Session.flush()

            form = datastore.Schema(
                name=u'test_schema',
                title=u'test_title',
                publish_date=date(2015, 1, 1)
            )

            Session.add(form)
            Session.flush()
