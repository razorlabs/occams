from sqlalchemy import DDL
from sqlalchemy import text

import hive.roster.upgrades.migrate as repository
from hive.roster import Session
from hive.roster import model
from hive.roster.base36 import base36decode


# Begin at the highest number that satisfies our specification
_IDSTART = base36decode('222222')


def importVarious(context):
    """ 
    GenericSetup conventional handle for importing miscellaneous steps.
    """
    if context.readDataFile('hive-roster.txt') is None:
        return
    portal = context.getSite()
    setupSQLDatabase(portal)


def setupSQLDatabase(portal):
    engine = Session.bind

    repository.install(engine)

    # Check to see if the sequence starts at 222-222, otherwise reset it
    last_value_query = text('SELECT last_value FROM identifier_id_pk_seq')
    (last_value,) = engine.execute(last_value_query).fetchone()

    if last_value < _IDSTART:
        # Alter the sequence to begin at 222-222
        alter_ddl = DDL(
            'ALTER SEQUENCE identifier_id_pk_seq RESTART WITH %d' % _IDSTART,
            on='postgres'
            )
        alter_ddl.execute(bind=engine)

    # Preset AEH site, this should be 
    site = Session.query(model.Site).filter_by(title=u'AEH').first()

    if site is None:
        site = model.Site(title=u'AEH')
        Session.add(site)
        Session.flush()
