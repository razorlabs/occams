""" 
Base 36 number conversion library
"""

def base36encode(number, alphabet='0123456789abcdefghijklmnopqrstuvwxyz'):
    """
    Convert positive integer to a base36 string.
    """
    if not isinstance(number, (int, long)):
        raise TypeError('number must be an integer')
    if number < 0:
        raise ValueError('number must be positive')

    # Special case for small numbers
    if number < 36:
        return alphabet[number]

    base36 = ''
    while number != 0:
        number, i = divmod(number, 36)
        base36 = alphabet[i] + base36

    return base36


def base36decode(number):
    return int(number, 36)
