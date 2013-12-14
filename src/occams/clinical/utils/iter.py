"""
Iterable tools
"""

from itertools import tee

try:
    # Using Python 2
    from itertools import ifilterfalse as filterfalse, ifilter as filter
except ImportError:
    # Using Python 3
    from itertools import filterfalse


def partition(predicate, iterable):
    """
    Itertools recipe to split an iterable by a predicate.
    """
    t1, t2 = tee(iterable)
    return filterfalse(predicate, t1), filter(predicate, t2)
