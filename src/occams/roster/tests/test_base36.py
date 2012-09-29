import unittest2 as unittest

from Products.CMFCore.utils import getToolByName

from occams.roster import testing
from occams.roster import base36


ALPHABET = '0123456789abcdefghijklmnopqrstuvwxyz'


class EncodeTestCase(unittest.TestCase):
    u"""
    Ensures that valid base 36 string representations can be generated
    """

    def test_non_numeric(self):
        with self.assertRaises(ValueError):
            base36.encode('X')

    def test_positive(self):
        for number in range(len(ALPHABET)):
            self.assertEqual(ALPHABET[number], base36.encode(number))

    def test_negative(self):
        for number in range(len(ALPHABET)):
            self.assertIn(ALPHABET[number], base36.encode(-number))

    def test_multidigit(self):
        self.assertEqual('1', base36.encode(1))
        self.assertEqual('a', base36.encode(10))
        self.assertEqual('2s', base36.encode(100))
        self.assertEqual('rs', base36.encode(1000))
        self.assertEqual('7ps', base36.encode(10000))
        self.assertEqual('255s', base36.encode(100000))
        self.assertEqual('lfls', base36.encode(1000000))
        self.assertEqual('gjdgxs', base36.encode(1000000000))
        self.assertEqual('cre66i9s', base36.encode(1000000000000))


class DecodeTestCase(unittest.TestCase):
    u"""
    Ensures base 36 string representations can be converted to base 10 integers
    """

    def test_invalid_string(self):
        with self.assertRaises(ValueError):
            base36.decode('!')

    def test_valid_string(self):
        for character in iter(ALPHABET):
            self.assertEqual(int(character, len(ALPHABET)), base36.decode(character))

