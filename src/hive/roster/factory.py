import re

from zope.interface import implements

from hive.roster.interfaces import IRegistry
from hive.roster import model
from hive.roster import Session


FILTER_RE = re.compile('0|1|l|o')

class Registry(object):
    implements(IRegistry)

    def create(self):
        # Hard-code for now
        site = Session.query(model.Site).filter_by(title=u'AEH').first()

        while True:
            identifier = model.Identifier(origin=site)
            Session.add(identifier)
            Session.flush()

            encoded = str(identifier)

            # prevent ambiguous number from being added to the database
            if FILTER_RE.search(encoded) is not None:
                identifier.is_active = False
                Session.flush()
            else:
                break

        return identifier


OURNumberFactory = Registry()
