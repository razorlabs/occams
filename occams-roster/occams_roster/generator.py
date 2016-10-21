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


def generate(db_session, site_name):
    """
    Generates an OUR number for the distributor
    """
    try:
        # attempt to find an existing site registration
        site = db_session.query(models.Site).filter_by(title=site_name).one()
    except NoResultFound:
        # none found, so automatically register the content
        site = models.Site(title=site_name)
        db_session.add(site)

    while True:
        identifier = models.Identifier(origin=site)
        db_session.add(identifier)
        db_session.flush()

        our_number = identifier.our_number

        if not OUR_PATTERN.match(our_number):
            identifier.is_active = False
            db_session.flush()
            continue

        return our_number
