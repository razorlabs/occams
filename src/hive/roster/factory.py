import re

from zope.interface import implements

from hive.roster.interfaces import IRegistry
from hive.roster import model
from hive.roster import Session


def isValidOurNumber(our_number):
    """
    Helper method to verify valid OUR numbers
    OUR Number Format:
        * No vowels
        * No ambiguous characters (1,l,0,o)
        * Two groups of three digits separated by a hyphen
    """
    our_format = re.compile(r"""
        [2-9bcdfghjkmnpqrstvwxz]{3}         # No vowels or ambiguous characters
        -                                   # Separator
        [2-9bcdfghjkmnpqrstvwxz]{3}         # No vowels or ambiguous characters
        """,
        re.IGNORECASE | re.VERBOSE
        )

    match = our_format.match(our_number)
    result = match is not None
    return result


class Registry(object):
    implements(IRegistry)

    def create(self):
        # Hard-code for now, ideally in the future it would be nice to get the
        # name from the actual site. Perhaps this can be implemented in the
        # future as a behavior.
        site = Session.query(model.Site).filter_by(title=u'AEH').first()

        while True:
            identifier = model.Identifier(origin=site)
            Session.add(identifier)

            # Flush so the identifier is assigned a primary key.
            Session.flush()

            encoded = str(identifier)

            # prevent ambiguous number from being added to the database
            if not isValidOurNumber(encoded):
                identifier.is_active = False
                Session.flush()
            else:
                break

        return identifier


OurNumberFactory = Registry()
