import argparse
import subprocess
import tempfile

from sqlalchemy import create_engine

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
  patientreference
  reftype
  schema
  site
  state
  string
  user
""".split()

POSTFIX = '_mrg'


def cleanup(engine):
    """
    Cleanup migration tables
    """
    print 'Cleaning up {0}'.format(engine.url.database)
    with engine.begin() as conn:
        for table in TABLES:
            merge_name = table + POSTFIX
            conn.execute('DROP TABLE IF EXISTS "{0}"'.format(merge_name))


def prepare(engine):
    """
    Creates the migration data
    """
    print 'Preparing database {0}'.format(engine.url.database)
    with engine.begin() as conn:
        for table in TABLES:
            print '{0}...'.format(table)
            merge_name = table + POSTFIX
            conn.execute('CREATE TABLE "{0}" (LIKE "{1}")'.format(merge_name, table))
            conn.execute('INSERT INTO "{0}" (SELECT * FROM "{1}")'.format(merge_name, table))


def migrate(src_engine, dst_engine):
    """
    Migrates the source data to the destination database
    """
    print 'Moving data  {0} -> {1}'.format(src_engine.url.database, dst_engine.url.database)
    with tempfile.NamedTemporaryFile('rw+b') as fp:
        pg_dump_args = ['pg_dump', '-O', '-U', src_engine.url.username, '-f', fp.name]
        for table in TABLES:
            pg_dump_args += ['-t', table + POSTFIX]
        pg_dump_args += [src_engine.url.database]

        subprocess.call(pg_dump_args)
        subprocess.call(['psql', '-U', dst_engine.url.username, '-f', fp.name, dst_engine.url.database])


def integrate(engine):
    """
    Incorporates the migration data into the system tables
    """
    print 'Integrating data at {0}'.format(engine.url.database)
    with engine.begin() as conn:
        print 'user...'
        conn.execute("""
            INSERT INTO "user" (key, create_date, modify_date)
            SELECT key, create_date, modify_date FROM "user_mrg"
            WHERE NOT EXISTS(SELECT 1 FROM "user" WHERE "user".key = "user_mrg".key)
            """)

        print 'schema...'
        conn.execute("""
            INSERT INTO "schema" (name, title, description, state, storage, publish_date, is_association, is_inline, create_date, modify_date, revision, create_user_id, modify_user_id)
            SELECT name, title, description, state, storage, publish_date, is_association, is_inline, create_date, modify_date, revision,
                (SELECT "user".id FROM "user" WHERE "user".key = (SELECT "user_mrg".key FROM "user_mrg" WHERE "user_mrg".id = create_user_id)),
                (SELECT "user".id FROM "user" WHERE "user".key = (SELECT "user_mrg".key FROM "user_mrg" WHERE "user_mrg".id = modify_user_id))
            FROM "schema_mrg"
            """)

        raise Exception




def main():
    src_engine = create_engine('postgresql://plone:pl0n3@localhost/mrg_phi')
    dst_engine = create_engine('postgresql://plone:pl0n3@localhost/mrg_fia')

    #cleanup(src_engine)
    #cleanup(dst_engine)

    #prepare(src_engine)
    #migrate(src_engine, dst_engine)
    integrate(dst_engine)

    #cleanup(src_engine)
    #cleanup(dst_engine)


if __name__ == '__main__':
    main()

