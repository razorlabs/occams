"""
Python object helpers
"""

from zope.component import adapter
from zope.interface import implementer
from zope.interface.common.mapping import IFullMapping
from zope.interface import providedBy
from zope.interface import directlyProvides
import zope.schema

from occams.datastore.interfaces import IEntity


class Item(object):
    """
    Base class for objects with an interface.
    """

    def __init__(self, **kwargs):
        """
        Constructor method that uses the schema's fields as key word arguments.
        """
        try:
            # If this object indeed has an interface we'll use it to
            # constraint the parameters
            iface = list(providedBy(self))[0]
        except KeyError:
            # Just a regular object
            pass
        else:
            for name in iface.names():
                setattr(self, name, kwargs.get(name))


def ItemFactory(iface, **kwargs):
    """
    Spawns objects from interface specifications.

    Arguments
        ``iface``
            A Zope-style Interface
        ``kwargs``:
            Values to apply to the newly created object
    """
    result = Item()
    directlyProvides(result, iface)

    for field_name, field in zope.schema.getFieldsInOrder(iface):
        # TODO: figure out how to use FieldProperty with this
        subkwargs = kwargs.get(field_name)
        if isinstance(field, zope.schema.Object) and subkwargs is not None:
            ## This is a subobject, and should be generated
            if isinstance(subkwargs, Item):
                ## hey now, I'm already an Instance object
                value = subkwargs
            else:
                value = ItemFactory(field.schema, **subkwargs)
        else:
            value = kwargs.get(field_name)
        result.__dict__[field_name] = value

    return result


# It just sounds cooler
spawn = ItemFactory


@adapter(IEntity)
@implementer(IFullMapping)
def entityToMapping(entity):
    """
    Converts an entity into a Python dictionary
    """
    result = dict()
    for key, value in entity.items():
        if entity.schema[key].type == 'object':
            value = entityToMapping(entity[key])
        result[key] = value
    return result
