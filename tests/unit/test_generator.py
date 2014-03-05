try:
    import unittest2 as unittest
except ImportError:
    import unittest

from ddt import ddt, data


def setup_module():
    """
    Intialize the connection for this module
    """
    from sqlalchemy import create_engine
    from occams.roster import Session, models
    Session.configure(bind=create_engine('sqlite:///:memory:'))
    models.Base.metadata.create_all(Session.bind)


class Fixture(unittest.TestCase):

    def tearDown(self):
        from occams.roster import Session
        import transaction
        transaction.abort()
        Session.remove()


@ddt
class OurNumberPaternTestCase(Fixture):
    """
    Checks that valid OUR numbers are being produced.
    """

    @data('222-22l',
          '222-l22',
          '222-22o',
          '222-o22',
          '222-220',
          '222-022',
          '222-221',
          '222-122')
    def test_ambiguous(self, number):
        """
        It should not allow ambigous numbers
        """
        from occams.roster.generator import OUR_PATTERN
        self.assertNotRegexpMatches(number, OUR_PATTERN)

    @data('222-a22',
          '222-e22',
          '222-i22',
          '222-o22',
          '222-u22',
          '222-y22',
          '222-fag')
    def test_vowels(self, number):
        """
        It should not allow vowels
        """
        from occams.roster.generator import OUR_PATTERN
        self.assertNotRegexpMatches(number, OUR_PATTERN)

    @data('222-22b',
          '222-22f',
          '222-22g')
    def test_valid(self, number):
        """
        It should allow valid numbers
        """
        from occams.roster.generator import OUR_PATTERN
        self.assertRegexpMatches(number, OUR_PATTERN)


class GeneratorTestCase(Fixture):

    def test_auto_create_site(self):
        """
        It should create an unregisterd site when generating an OUR number
        """
        from occams.roster import generate, Session, models, OUR_PATTERN
        our_number = generate(u'AEH')
        self.assertRegexpMatches(our_number, OUR_PATTERN)
        self.assertEqual(1, Session.query(models.Site).count())

    def test_existing_site(self):
        """
        It should re-use previously registered sites
        """
        from occams.roster import generate, Session, models, OUR_PATTERN
        Session.add(models.Site(title=u'AEH'))
        Session.flush()

        our_number = generate(u'AEH')
        self.assertRegexpMatches(our_number, OUR_PATTERN)
        self.assertEqual(1, Session.query(models.Site).count())

    def test_issues_only_valid_our_numbers(self):
        """
        It should only generate valid OUR numbers
        """
        from occams.roster import generate, Session, models, OUR_PATTERN
        # eventually it will create an invalid one and mark is as invactive
        for i in range(100):
            generate(u'AEH')
        invalids_query = (
            Session.query(models.Identifier)
            .filter_by(is_active=False))
        valids_query = (
            Session.query(models.Identifier)
            .filter_by(is_active=True))
        self.assertLessEqual(1, invalids_query.count())
        for record in invalids_query:
            self.assertNotRegexpMatches(record.our_number, OUR_PATTERN)
        for record in valids_query:
            self.assertRegexpMatches(record.our_number, OUR_PATTERN)
