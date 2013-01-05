u"""
Base 36 number conversion library
"""

ALPHABET = '0123456789abcdefghijklmnopqrstuvwxyz'


def encode(number):
    u"""
    Convert integer to a base36 string.

    """
    # save the sign for later
    sign = '' if int(number) >= 0 else '-'
    number = abs(int(number))
    base36 = '' if number > 0 else '0'

    # keep dividing until zero, using the mod as the character position
    while number != 0:
        number, mod = divmod(number, len(ALPHABET))
        base36 = ALPHABET[mod] + base36

    return sign + base36


def decode(number):
    u"""
    Convert a base 36 string back to a base 10 integer.
    Raises:
        ``ValueError`` if the value is not alphanumeric
    """
    return int(number, len(ALPHABET))

