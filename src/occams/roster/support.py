from sqlalchemy import orm
from zope import interface
from zope import component

from occams.roster import interfaces
from occams.roster import model
from occams.roster import Session


def verify_our_number(number):
    u"""
    Helper method to verify valid OUR numbers
    """
    return interfaces.OUR_PATTERN.match(number) is not None


class OurNumberSupport(object):
    interface.implements(interfaces.IOurNumberSupport)
    component.adapts(interfaces.IOurNumberDistributor)

    __doc__ = interfaces.IOurNumberSupport.__doc__

    def __init__(self, context):
        self.context = context

    def generate(self):
        session = Session()
        site_name = self.context.get_source_name()
        our_number  = None

        try:
            # attempt to find an existing site registration
            site = session.query(model.Site).filter_by(title=site_name).one()
        except orm.exc.NoResultFound:
            # none found, so automatically register the content
            site = model.Site(title=site_name)

        while our_number is None:
            identifier = model.Identifier(origin=site)
            session.add(identifier)
            session.flush()

            our_number = identifier.our_number

            if not verify_our_number(our_number):
                our_number = None
                identifier.is_active = False
                session.flush()

        return our_number

