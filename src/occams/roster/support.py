from sqlalchemy import orm
from zope import interface

from occams.roster import interfaces
from occams.roster import model
from occams.roster import Session


def verify_our_number(number):
    u"""
    Helper method to verify valid OUR numbers
    """
    return interfaces.OUR_PATTERN.match(number) is not None


class OurNumberSupport(object):

    def __init__(self, context):
        self.context = context

    def generate(self):
        session = Session()
        site_name = self.context.site_name
        our_number  = None

        try:
            site = session.query(model.Site).filter_by(title=site_name).one()
        except orm.exc.NoResultFound:
            site = model.Site(title=site_name)

        while our_number is None:
            identifier = model.Identifier(origin=site)
            session.add(identifier)
            session.flush()

            our_number = identifier.our_number

            if not verify_our_number(our_number):
                identifier.is_active = False
                session.flush()
                our_number = None

        return our_number

