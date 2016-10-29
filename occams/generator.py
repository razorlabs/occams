import re

from sqlalchemy.orm.exc import NoResultFound

from . import models


OUR_PATTERN = re.compile(
    r"""
    [2-9bcdfghjkmnpqrstvwxz]{3}         # No vowels or ambiguous characters
    -                                   # Separator
    [2-9bcdfghjkmnpqrstvwxz]{3}         # No vowels or ambiguous characters
    """,
    re.IGNORECASE | re.VERBOSE)


def generate(dbsession, site_name):
    """
    Generates an OUR number for the distributor
    """
    try:
        # attempt to find an existing site registration
        site = dbsession.query(models.RosterSite).filter_by(title=site_name).one()
    except NoResultFound:
        # none found, so automatically register the content
        site = models.RosterSite(title=site_name)
        dbsession.add(site)

    while True:
        identifier = models.Identifier(origin=site)
        dbsession.add(identifier)
        dbsession.flush()

        our_number = identifier.our_number

        if not OUR_PATTERN.match(our_number):
            identifier.is_active = False
            dbsession.flush()
            continue

        return our_number
