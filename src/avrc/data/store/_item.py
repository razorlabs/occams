""" Defines useful base items for interface implementations.

    At some point in the future we'll probably get rid of the implementations
    and just rely on these base classes.
"""

from zope.interface import providedBy


class AbstractItem(object):
    """ Base class for items.
    """

    def __init__(self, **kwargs):
        """ Creates a new item.

            Allowed keyword arguments are field names in the target interface.
        """
        try:
            for name in list(providedBy(self))[0].names():
                if name in kwargs:
                    setattr(self, name, kwargs.get(name))
        except IndexError:
            pass