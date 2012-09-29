import unittest2 as unittest

from zope import interface

from occams.roster import testing
from occams.roster import support
from occams.roster import interfaces


class VerityOurNumberTestCase(unittest.TestCase):
    u"""
    Checks that valid OUR numbers are being produced.
    """

    def test_ambiguous(self):
        numbers = (
            u'222-22l',
            u'222-l22',
            u'222-22o',
            u'222-o22',
            u'222-220',
            u'222-022',
            u'222-221',
            u'222-122',
            )

        for number in numbers:
            self.assertFalse(
                support.verify_our_number(number),
                msg='%s is unexpectedly valid' % number
                )

    def test_vowels(self):
        numbers = (
            # vowels
            u'222-a22',
            u'222-e22',
            u'222-i22',
            u'222-o22',
            u'222-u22',
            u'222-y22',
            u'222-fag',
            )

        for number in numbers:
            self.assertFalse(
                support.verify_our_number(number),
                msg='%s is unexpectedly valid' % number
                )

    def test_valid(self):
        numbers = (
            u'222-22b',
            u'222-22f',
            u'222-22g',
            )

        for number in numbers:
            self.assertTrue(
                support.verify_our_number(number),
                msg='%s is unexpectedly invalid' % number
                )


class ObliviousContent(object):
    u"""
    A content item that doesn't know it can assign OUR numbers
    """


interface.alsoProvides(ObliviousContent, interfaces.IOurDistributeable)


class OurNumberSupportTestCase(unittest.TestCase):

    layer = testing.OCCAMS_ROSTER_INTEGRATION_TESTING

    def test_sketch(self):
        u"""
        Testing if this even works
        """
        item = ObliviousContent()
        assign = interfaces.IOurNumberSupport(item)
        our_number = assign.generate()
        self.assertRegexpMatches(our_number, r'\w\w\w-\w\w\w')

