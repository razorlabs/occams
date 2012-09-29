from occams.roster.upgrades import migrate as repository
from occams.roster import Session


def import_various(context):
    u"""
    GenericSetup conventional handle for importing miscellaneous steps.
    """
    if context.readDataFile('occams-roster.txt') is not None:
        portal = context.getSite()
        setup_database(portal)


def setup_database(portal):
    session = Session()
    engine = session.bind
    repository.install(engine)

