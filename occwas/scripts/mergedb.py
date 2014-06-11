"""
Merges legacy PHI and FIA databases

The target database's attribute column will gain a ``is_private``
column in order to differentiate between private information.

THIS SCRIPT SOULD BE RUN BEFORE ANY UPGRADING TAKES PLACE!
"""

import argparse
from subprocess import check_call
import tempfile

import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL

ECHO = False

# These are the only tables in the PHI database that will contain data
TABLES = """
  attribute
  blob
  choice
  context
  datetime
  decimal
  entity
  integer
  object
  partner
  patient
  schema
  string
  text
  user
""".split()

# These tables need to keep track of which database they came from so that
# they can be easily updated without trying to figure out their unique
# features as some of them don't have them
TRACK = set([
    'partner',
    'arm', 'cycle', 'enrollment', 'patientreference',
    'reftype', 'site', 'stratum', 'study', 'visit',
    'attribute', 'blob', 'category', 'choice',
    'datetime', 'decimal', 'entity', 'integer',
    'schema', 'string', 'text', 'object',
    'context'])

LAB_TRACK = set([
    'aliquot', 'aliquotstate', 'aliquottype',
    'location', 'specialinstruction',
    'specimen', 'specimenstate', 'specimentype'])

CCTG_TRACK = set(['patient_log', 'patient_log_nonresponse_type'])


def mrg(table):
    """
    Returns the "merge" name for a table
    """
    return table + '_mrg'


cli = argparse.ArgumentParser(description='Merges PHI and FIA')
cli.add_argument('-U', dest='user', metavar='USER:PW')
cli.add_argument('-O', dest='owner', metavar='OWNER:PW')
cli.add_argument('--phi', metavar='DB', help='PHI database')
cli.add_argument('--fia', metavar='DB', help='FIA database')
cli.add_argument('--target', metavar='DB', help='Merged database')


def main():
    args = cli.parse_args()

    uid, upw = args.user.split(':')
    oid, opw = args.owner.split(':')

    phi = URL('postgresql', username=oid, password=opw, database=args.phi)
    fia = URL('postgresql', username=oid, password=opw, database=args.fia)
    target = URL('postgresql', username=oid, password=opw, database=args.target)

    print('FIA -> {0}'.format(repr(fia)))
    print('PHI -> {0}'.format(repr(phi)))
    print('TARGET -> {0}'.format(repr(target)))

    if any(dbname in target.database for dbname in ['aeh', 'cctg', 'mhealth']):
        TRACK.update(LAB_TRACK)

    if 'cctg' in target.database:
        TRACK.update(CCTG_TRACK)

    copy(uid, upw, fia, target)

    cleanup(phi)
    cleanup(fia)
    cleanup(target)

    prepare(phi)

    track(phi,  phi.database, [mrg(t) for t in TABLES if t in TRACK])
    track(target, fia.database, TRACK)

    migrate(phi, target, TABLES)
    integrate(target)

    cleanup(phi)
    cleanup(fia)
    cleanup(target)


def cleanup(url):
    """
    Cleanup migration tables
    """
    print('Cleaning up {0}'.format(url.database))
    engine = create_engine(url, echo=ECHO)
    with engine.begin() as conn:
        for table in TABLES:
            conn.execute('DROP TABLE IF EXISTS "{0}"'.format(mrg(table)))


def prepare(url):
    """
    Creates the migration data
    """
    print('Preparing database {0}'.format(url.database))

    engine = create_engine(url, echo=ECHO)

    with engine.begin() as conn:
        for table in TABLES:
            print('{0}...'.format(table))
            conn.execute('CREATE TABLE "{0}" (LIKE "{1}")'
                         .format(mrg(table), table))
            conn.execute('INSERT INTO "{0}" (SELECT * FROM "{1}")'
                         .format(mrg(table), table))


def track(url, old_db, tables):
    """
    Tracks values in a new database based on their old database pks
    """
    print('Tracking tables at {0}'.format(url.database))
    engine = create_engine(url, echo=ECHO)
    with engine.begin() as conn:
        for table in tables:
            print('{0}...'.format(table))
            conn.execute('ALTER TABLE {0} ADD old_db VARCHAR'
                         .format(table))
            conn.execute('ALTER TABLE {0} ADD old_id INTEGER'
                         .format(table))
            conn.execute('ALTER TABLE {0} ADD UNIQUE (old_db, old_id)'
                         .format(table))
            conn.execute('UPDATE {0} SET old_db = \'{1}\' , old_id = id'
                         .format(table, old_db))
            conn.execute('ALTER TABLE {0} ALTER old_db SET NOT NULL'
                         .format(table))
            conn.execute('ALTER TABLE {0} ALTER old_id SET NOT NULL'
                         .format(table))


def copy(suid, supw, src, dst):
    """
    Makes a copy of the src (i.e. FIA) database to use as a base
    """
    print('Copying {0} -> {1}'.format(src.database, dst.database))
    conn = psycopg2.connect(user=suid,
                            password=supw,
                            host=src.host,
                            port=src.port,
                            database=src.database)
    conn.set_isolation_level(0)
    cursor = conn.cursor()
    cursor.execute('DROP DATABASE IF EXISTS {dstdb}'
                   .format(dstdb=dst.database))
    cursor.execute('CREATE DATABASE {dstdb} WITH OWNER {username} TEMPLATE {srcdb}'
                   .format(dstdb=dst.database, srcdb=src.database, username=dst.username))
    conn.commit()
    cursor.close()
    conn.close()


def migrate(src, dst, tables):
    """
    Migrates the source data to the destination database
    """
    print('Moving data {0} -> {1}'.format(src.database, dst.database))

    with tempfile.NamedTemporaryFile('rw+b') as fp:
        pg_dump = ['/usr/pgsql-9.3/bin/pg_dump', '-f', fp.name, '--no-owner']
        for table in tables:
            pg_dump += ['-t', mrg(table)]
        pg_dump += ['-d', str(src)]

        check_call(pg_dump)
        check_call(['/usr/pgsql-9.3/bin/psql', '-f', fp.name, '-d', str(dst)])


def integrate(url):
    """
    Incorporates the migration data into the system tables
    """
    print('Integrating data at {0}'.format(url.database))
    engine = create_engine(url, echo=ECHO)
    with engine.begin() as conn:
        for table in TABLES:
            conn.execute('ALTER TABLE "{0}" ADD mrg_id INT UNIQUE'
                         .format(table))

        for table in ('attribute', 'attribute_audit'):
            conn.execute('ALTER TABLE {0} ADD is_private BOOLEAN'
                         .format(table))
            conn.execute('UPDATE {0} SET is_private = FALSE'
                         .format(table))
            conn.execute('ALTER TABLE {0} ALTER is_private SET NOT NULL'
                         .format(table))

        # User/patient are shared in both systems, so just update the mapping
        # key
        print('user...')
        conn.execute("""
            UPDATE "user"
            SET mrg_id = (
                SELECT id
                FROM "user_mrg"
                WHERE "user_mrg".key = "user".key)
            """)

        print('patient...')
        conn.execute("""
            UPDATE "patient"
            SET mrg_id = (
                SELECT id
                FROM "patient_mrg"
                WHERE "patient".zid = "patient_mrg".zid)
            """)

        print('partner...')
        conn.execute("""
            INSERT INTO "partner" (
                mrg_id, zid,
                patient_id, enrolled_patient_id,
                report_date,
                create_date, modify_date, revision,
                create_user_id, modify_user_id,
                old_db, old_id)
            SELECT
                id, zid,
                (SELECT id FROM "patient" WHERE mrg_id = patient_id),
                (SELECT id FROM "patient" WHERE mrg_id = enrolled_patient_id),
                report_date,
                create_date, modify_date, revision,
                (SELECT id FROM "user" WHERE mrg_id = create_user_id),
                (SELECT id FROM "user" WHERE mrg_id = modify_user_id),
                old_db, old_id
            FROM "partner_mrg"
            """)

        print('schema...')
        conn.execute("""
            INSERT INTO "schema" (
                mrg_id, name, title, description,
                storage, publish_date, state, is_inline,
                create_date, modify_date, revision,
                create_user_id, modify_user_id,
                old_db, old_id)
            SELECT
                id, name, title, description,
                storage, publish_date, state, is_inline,
                create_date, modify_date, revision,
                (SELECT id FROM "user" WHERE mrg_id = create_user_id),
                (SELECT id FROM "user" WHERE mrg_id = modify_user_id),
                old_db, old_id
            FROM "schema_mrg"
            """)

        print('attribute...')
        conn.execute("""
            INSERT INTO "attribute" (
                mrg_id, name, title, description,
                type, is_private, is_collection, is_required,
                checksum, "order",
                schema_id,
                object_schema_id,
                create_date, modify_date, revision,
                create_user_id, modify_user_id,
                old_db, old_id)
            SELECT
                id, name, title, description,
                type, TRUE, is_collection, is_required, checksum, "order",
                (SELECT id FROM "schema" WHERE mrg_id = schema_id),
                (SELECT id FROM "schema" WHERE mrg_id = object_schema_id),
                create_date, modify_date, revision,
                (SELECT id FROM "user" WHERE mrg_id = create_user_id),
                (SELECT id FROM "user" WHERE mrg_id = modify_user_id),
                old_db, old_id
            FROM "attribute_mrg"
            """)

        print('choice...')
        conn.execute("""
            INSERT INTO "choice" (
                mrg_id, name, title, description,
                value, "order",
                attribute_id,
                create_date, modify_date, revision,
                create_user_id, modify_user_id,
                old_db, old_id)
            SELECT
                id, name, title, description,
                value, "order",
                (SELECT id FROM "attribute" WHERE mrg_id = attribute_id),
                create_date, modify_date, revision,
                (SELECT id FROM "user" WHERE mrg_id = create_user_id),
                (SELECT id FROM "user" WHERE mrg_id = modify_user_id),
                old_db, old_id
            FROM "choice_mrg"
            """)

        print('entity...')
        conn.execute("""
            INSERT INTO "entity" (
                mrg_id, name, title, description, state, collect_date,
                schema_id,
                create_date, modify_date, revision,
                create_user_id, modify_user_id,
                old_db, old_id)
            SELECT
                id, name, title, description, state, collect_date,
                (SELECT id FROM "schema" WHERE mrg_id = schema_id),
                create_date, modify_date, revision,
                (SELECT id FROM "user" WHERE mrg_id = create_user_id),
                (SELECT id FROM "user" WHERE mrg_id = modify_user_id),
                old_db, old_id
            FROM "entity_mrg"
            """)

        for value in ('datetime', 'integer', 'blob', 'text',
                      'decimal', 'string', 'object'):
            print(value + '...')

            if value == 'object':
                value_getter = '(SELECT id FROM "entity" WHERE mrg_id = value)'
            else:
                value_getter = 'value'

            conn.execute("""
                INSERT INTO "{0}" (
                    mrg_id,
                    entity_id,
                    attribute_id,
                    choice_id,
                    value,
                    create_date, modify_date, revision,
                    create_user_id, modify_user_id,
                    old_db, old_id)
                SELECT
                    id,
                    (SELECT id FROM "entity" WHERE mrg_id = entity_id),
                    (SELECT id FROM "attribute" WHERE mrg_id = attribute_id),
                    (SELECT id FROM "choice" WHERE mrg_id = choice_id),
                    {1},
                    create_date, modify_date, revision,
                    (SELECT id FROM "user" WHERE mrg_id = create_user_id),
                    (SELECT id FROM "user" WHERE mrg_id = modify_user_id),
                    old_db, old_id

                FROM "{0}_mrg"
                """.format(value, value_getter))

        print('context...')
        for row in conn.execute('SELECT DISTINCT external FROM context_mrg'):
            conn.execute("""
                INSERT INTO context (
                    mrg_id,
                    entity_id,
                    external,
                    key,
                    create_date, modify_date, revision,
                    create_user_id, modify_user_id,
                    old_db, old_id)
                SELECT
                    id,
                    (SELECT id FROM "entity" WHERE mrg_id = entity_id),
                    external,
                    (SELECT id FROM "{0}" WHERE mrg_id = key),
                    create_date, modify_date, revision,
                    (SELECT id FROM "user" WHERE mrg_id = create_user_id),
                    (SELECT id FROM "user" WHERE mrg_id = modify_user_id),
                    old_db, old_id
                FROM "context_mrg"
                WHERE external = '{0}'
                AND EXISTS( SELECT 1 FROM "{0}" WHERE mrg_id = key )
                """.format(row['external']))

        for table in TABLES:
            conn.execute('ALTER TABLE "{0}" DROP COLUMN mrg_id'.format(table))

        # EarlyTest.someone_had_early_test is PHI, but in FIA
        conn.execute("""
            UPDATE attribute
            SET is_private = TRUE
            WHERE attribute.name = 'someone_had_early_test'
            """)


if __name__ == '__main__':
    main()
