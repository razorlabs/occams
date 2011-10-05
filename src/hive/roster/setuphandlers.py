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

    vendorSetupMap = dict(
        postgresql=setupPostgreSql,
        sqlite=setupSqlite,
        )

    # Preset AEH site, this should be 
    site = Session.query(model.Site).filter_by(title=u'AEH').first()

    if site is None:
        site = model.Site(title=u'AEH')
        Session.add(site)
        Session.flush()

    if engine.name not in vendorSetupMap:
        raise Exception('Unsupported database vendor: %s' % engine.name)
    else:
        # Setup primary key start (SQLAlchemy doesn't do this automatically)
        setupFunction = vendorSetupMap.get(engine.name)
        setupFunction()


def setupPostgreSql():
    """ 
    Sets up the start number on PostgreSQL by modifying the SEQUENCE
    """
    engine = Session.bind
    # Check to see if the sequence starts at 222-222, otherwise reset it
    last_value_query = text('SELECT last_value FROM identifier_id_pk_seq')
    (last_value,) = engine.execute(last_value_query).fetchone()

    if last_value < _IDSTART:
        # Alter the sequence to begin at 222-222
        alter_ddl = DDL(
            'ALTER SEQUENCE identifier_id_pk_seq RESTART WITH %d' % _IDSTART
            )
        alter_ddl.execute(bind=engine)


def setupSqlite():
    """
    Sets up the start number on SQLite by inserting a dummy entry to bump
    primary key index (this number is deleted afterwards)
    """
    engine = Session.bind
    identifier = (
        Session.query(model.Identifier)
        .order_by(model.Identifier.id.desc())
        .first()
        )

    if identifier is None or identifier.id < _IDSTART:
        # One before the number we ACTUALLY want to start at
        stub = _IDSTART - 1
        site = Session.query(model.Site).order_by(model.Site.id.asc()).first()
        identifier = model.Identifier(id=stub, origin=site, is_active=False)
        # Temporarily add the new identifier
        Session.add(identifier)
        Session.flush()
        # Now remove it
        Session.delete(identifier)
        Session.flush()
