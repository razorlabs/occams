from sqlalchemy import DDL
from sqlalchemy import text

import hive.roster.upgrades.migrate as repository
from hive.roster import Session
from hive.roster import model
from hive.roster.interfaces import START_ID


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
    lastValueQuery = text('SELECT last_value FROM identifier_id_pk_seq')
    (lastValue,) = engine.execute(lastValueQuery).fetchone()

    if lastValue < START_ID:
        # Alter the sequence to begin at 222-222
        queryTemplate = 'ALTER SEQUENCE identifier_id_pk_seq RESTART WITH %d'
        DDL(queryTemplate % START_ID).execute(bind=engine)


def setupSqlite():
    """
    Sets up the start number on SQLite by inserting a dummy entry to bump
    primary key index (this number is deleted afterwards)
    """
    engine = Session.bind
    engine.echo = True
    identifierTableName = model.Identifier.__tablename__
    siteTableName = model.Site.__tablename__
    lastValueQuery = text('SELECT MAX(id) FROM %s' % identifierTableName)
    (lastValue,) = engine.execute(lastValueQuery).fetchone()
    siteIdQuery = text('SELECT MIN(id) FROM %s' % siteTableName)
    (siteId,) = engine.execute(siteIdQuery).fetchone()

    if lastValue < START_ID:
        # Start before the one we actually want, so sequence picks up the next one
        startId = START_ID - 1
        queryTemplate = (
            'INSERT INTO %s (id, origin_id, is_active, create_date, modify_date) '
            'VALUES (%d, %d, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP) '
            )
        DDL(queryTemplate % (identifierTableName, startId, siteId)).execute(bind=engine)

        # Now delete the entry so we can start fresh
        queryTemplate = 'DELETE FROM %s WHERE id = %d'
        DDL(queryTemplate % (identifierTableName, startId)).execute(bind=engine)
