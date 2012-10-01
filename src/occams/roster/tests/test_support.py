import unittest2 as unittest

from zope import interface

from occams.roster import testing
from occams.roster import support
from occams.roster import model
from occams.roster import interfaces
from occams.roster import Session


class VerityOurNumberTestCase(unittest.TestCase):
    u"""
    Checks that valid OUR numbers are being produced.
    """

    def test_ambiguous(self):
        numbers = [
            u'222-22l',
            u'222-l22',
            u'222-22o',
            u'222-o22',
            u'222-220',
            u'222-022',
            u'222-221',
            u'222-122',
            ]

        for number in numbers:
            self.assertFalse(
                support.verify_our_number(number),
                msg='%s is unexpectedly valid' % number
                )

    def test_vowels(self):
        numbers = [
            u'222-a22',
            u'222-e22',
            u'222-i22',
            u'222-o22',
            u'222-u22',
            u'222-y22',
            u'222-fag',
            ]

        for number in numbers:
            self.assertFalse(
                support.verify_our_number(number),
                msg='%s is unexpectedly valid' % number
                )

    def test_valid(self):
        numbers = [
            u'222-22b',
            u'222-22f',
            u'222-22g',
            ]

        for number in numbers:
            self.assertTrue(
                support.verify_our_number(number),
                msg='%s is unexpectedly invalid' % number
                )


class ObliviousItem(object):
    u"""
    A content item that doesn't know it can assign OUR numbers
    """

    def __init__(self, name):
        self.name = name


class ObliviousHelper(object):
    u"""
    A helper class that allows the ``ObliviousItem to distribute OUR numbers
    """
    interface.implements(interfaces.IOurNumberDistributor)

    def __init__(self, context):
        self.context = context

    def get_source_name(self):
        return self.context.name


class OurNumberSupportTestCase(unittest.TestCase):

    layer = testing.OCCAMS_ROSTER_INTEGRATION_TESTING

    def test_auto_create_site(self):
        u"""
        Issuing an OUR number from an unregistered site will auto-register it
        """
        session = Session()
        item = ObliviousItem(u'AEH')
        helper = ObliviousHelper(item)
        assign = interfaces.IOurNumberSupport(helper)
        our_number = assign.generate()
        self.assertRegexpMatches(our_number, r'\w\w\w-\w\w\w')
        self.assertEqual(1, session.query(model.Site).count())

    def test_existing_site(self):
        u"""
        Issuing an OUR number from a registered site by it's name
        """
        session = Session()
        session.add(model.Site(title=u'AEH'))
        session.flush()
        item = ObliviousItem(u'AEH')
        helper = ObliviousHelper(item)
        assign = interfaces.IOurNumberSupport(helper)
        our_number = assign.generate()
        self.assertRegexpMatches(our_number, r'\w\w\w-\w\w\w')
        # no new site crated
        self.assertEqual(1, session.query(model.Site).count())

    def test_issues_only_valid_our_numbers(self):
        u"""
        Only valid OUR numbers are issued by the utility
        """
        session = Session()
        # eventually it will create an invalid one and mark is as invactive
        for i in range(100):
            item = ObliviousItem(u'ABCD')
            helper = ObliviousHelper(item)
            assign = interfaces.IOurNumberSupport(helper)
            our_number = assign.generate()
        invalids_query = session.query(model.Identifier).filter_by(is_active=False)
        self.assertLessEqual(1, invalids_query.count())

