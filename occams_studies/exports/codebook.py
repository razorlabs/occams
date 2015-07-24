"""
Code Book Utilities
"""

# Convenience header for passing to csv's dictrow function
HEADER = [
    'table',
    'form',
    'publish_date',
    'field',
    'title',
    'description',
    'is_required',
    'is_system',
    'is_collection',
    'is_private',
    'type',
    'decimal_places',
    'choices',
    'order',
    ]


# File name for the generated codebook
FILE_NAME = 'codebook.csv'


class types:
    """
    Enum of constant strings for each supported type
    """

    BOOLEAN = 'boolean'
    CHOICE = 'choice'
    STRING = 'string'
    TEXT = 'text'
    FILE = 'file'
    DATE = 'date'
    DATETIME = 'datetime'
    TIME = 'time'
    NUMBER = 'number'


def row(
    field,
    table,
    type,
    decimal_places=None,
    choices=[],
    form=None,
    publish_date=None,
    title=None,
    desc=None,
    order=None,
    is_system=False,
    is_required=False,
    is_collection=False,
    is_private=False
):
    """
    Helper function to create an codebook row entry
    """

    # Legacy fix, our clients don't understand BLOB
    if type.lower() == 'blob':
        type = types.FILE

    return {
        'field':          field,
        'table':          table,
        'type':           type,
        'decimal_places': decimal_places,
        'form':           form,
        'publish_date':   publish_date,
        'title':          title,
        'description':    desc,
        'is_system':      is_system,
        'is_required':    is_required,
        'is_collection':  is_collection,
        'is_private':     is_private,
        'choices':        sorted(choices, key=lambda c: int(c[0])),
        'order':          order
    }
