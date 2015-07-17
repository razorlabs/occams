"""
Code Book Utitlities

Column format
-------------

Each entry in the code book is a column in the eCRF listed under "table".

All eCRFs must contain the following system variables:

=============== =================== ===========================================
Column Name     Example             Description
=============== =================== ===========================================
table           sample_ecrf         The system name for the eCRF, which will be
                                    used as the file name of the data file.

form            Sample eCRF         The display/printable title of the eCRF.

publish_date    2015-07-01          The version of the eCRF.
                                    Values must be in ISO-8601 format
                                    (i.e. YYYY-MM-DD)

field           myvar               The variable name of the field.

title           My Variable         The printed question for the field.

description     Long description    A longer help text for the field.(optional)

is_required     TRUE                Flag indicating that the field is required
                                    during data entry.

                                    Possible values are: TRUE or FALSE

is_system       FALSE               Flag indicating that the field is managed
                                    by the system.

                                    Possible values are: TRUE or FALSE

is_collection   FALSE               Flag indicating that the field can have
                                    multiple selections. This is only
                                    applicable to "choice" fields.

                                    Possible values are: TRUE or FALSE

is_private      TRUE                Flag indicating that the field contains
                                    sensitive subject information.

                                    Possible values are: TRUE or FALSE

type            string              The data type for the variable.

                                    Possible values are:
                                        boolean
                                        choice
                                        string
                                        text
                                        blob
                                        date
                                        datetime
                                        numeric

choices         0=No;1=Yes;2=N/A    Available answer choices for the field.
                                    This only applies to variables of
                                    type "choice".
                                    Each answer choice is a numeric code
                                    followed by an equals (=) sign followed
                                    by the displayed label, delimited by
                                    semi-colon.

                                    Please note that order is important.

order           3                   The display order of the field.
                                    Does not apply to system variables.

=============== =================== ===========================================

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
    BLOB = 'blob'
    DATE = 'date'
    DATETIME = 'datetime'
    TIME = 'time'
    NUMERIC = 'numeric'


def row(
    field,
    table,
    type,
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

    return {
        'field':          field,
        'table':          table,
        'type':           type,
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
