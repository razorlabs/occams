import pytest


class TestOurNumberPatern:
    """
    Checks that valid OUR numbers are being produced.
    """

    @pytest.mark.parametrize('number', [
        '222-22l',
        '222-l22',
        '222-22o',
        '222-o22',
        '222-220',
        '222-022',
        '222-221',
        '222-122'])
    def test_ambiguous(self, number):
        """
        It should not allow ambigous numbers
        """
        from occams_roster.generator import OUR_PATTERN
        assert not OUR_PATTERN.match(number)

    @pytest.mark.parametrize('number', [
        '222-a22',
        '222-e22',
        '222-i22',
        '222-o22',
        '222-u22',
        '222-y22',
        '222-fag'])
    def test_vowels(self, number):
        """
        It should not allow vowels
        """
        from occams_roster.generator import OUR_PATTERN
        assert not OUR_PATTERN.match(number)
        assert not OUR_PATTERN.match(number)

    @pytest.mark.parametrize('number', [
        '222-22b',
        '222-22f',
        '222-22g'])
    def test_valid(self, number):
        """
        It should allow valid numbers
        """
        from occams_roster.generator import OUR_PATTERN
        assert OUR_PATTERN.match(number)


class TestGenerator:

    def test_auto_create_site(self, db_session):
        """
        It should create an unregisterd site when generating an OUR number
        """
        from occams_roster import generate, models, OUR_PATTERN
        res = generate(db_session, u'AEH')
        assert OUR_PATTERN.match(res)
        assert 1 == db_session.query(models.Site).count()

    def test_existing_site(self, db_session):
        """
        It should re-use previously registered sites
        """
        from occams_roster import generate, models, OUR_PATTERN
        db_session.add(models.Site(title=u'AEH'))
        db_session.flush()

        res = generate(db_session, u'AEH')
        assert OUR_PATTERN.match(res)
        assert 1 == db_session.query(models.Site).count()

    def test_issues_only_valid_our_numbers(self, db_session):
        """
        It should only generate valid OUR numbers
        """
        from occams_roster import generate, models, OUR_PATTERN
        # eventually it will create an invalid one and mark is as invactive
        for i in range(100):
            generate(db_session, u'AEH')
        invalids_query = (
            db_session.query(models.Identifier)
            .filter_by(is_active=False))
        valids_query = (
            db_session.query(models.Identifier)
            .filter_by(is_active=True))
        assert invalids_query.count() >= 1
        for record in invalids_query:
            res = record.our_number
            assert not OUR_PATTERN.match(res)
        for record in valids_query:
            res = record.our_number
            assert OUR_PATTERN.match(res)
