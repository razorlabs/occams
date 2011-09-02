import unittest

from hive.roster.factory import isValidOurNumber


class OurNumberTestCase(unittest.TestCase):
    """
    Checks that valid OUR numbers are being produced.
    """

    def test_validator(self):
        invalid_numbers = (
            # ambiguous characters
            '222-22l',
            '222-l22',
            '222-22o',
            '222-o22',
            '222-220',
            '222-022',
            '222-221',
            '222-122',
            # vowels
            '222-a22',
            '222-e22',
            '222-i22',
            '222-o22',
            '222-u22',
            '222-y22',
            )

        valid_numbers = (
            '222-22a',
            '222-22e',
            '222-22i',
            '222-22u',
            '222-22y',
            )

        for number in invalid_numbers:
            self.assertFalse(isValidOurNumber(number))

        for number in valid_numbers:
            self.assertTrue(isValidOurNumber(number))

