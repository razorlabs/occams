"""
Merges legacy PHI and FIA databases

The target database's attribute column will gain a ``is_private`` column in order
to differentiate between private information.

THIS SCRIPT SOULD BE RUN BEFORE ANY UPGRADING TAKES PLACE!
"""

import argparse
import subprocess
import tempfile

from sqlalchemy import create_engine

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

POSTFIX = '_mrg'

cli = argparse.ArgumentParser(description='Merges PHI into FIA')
cli.add_argument('phi', metavar='PHIDB', type=create_engine, help='PHI database')
cli.add_argument('fia', metavar='FIADB', type=create_engine, help='FIA database')


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
        for table in TABLES:
            conn.execute('ALTER TABLE "{0}" ADD COLUMN mrg_id INT UNIQUE'.format(table))

        conn.execute('ALTER TABLE "attribute" ADD COLUMN is_private BOOLEAN')
        conn.execute('ALTER TABLE "attribute_audit" ADD COLUMN is_private BOOLEAN')
        conn.execute('UPDATE "attribute" SET is_private = FALSE')
        conn.execute('UPDATE "attribute_audit" SET is_private = FALSE')
        conn.execute('ALTER TABLE "attribute" ALTER is_private SET NOT NULL')
        conn.execute('ALTER TABLE "attribute_audit" ALTER is_private SET NOT NULL')

        # User/patient are shared in both systems, so just update the mapping key
        print 'user...'
        conn.execute("""
            UPDATE "user"
            SET mrg_id = (
                SELECT id
                FROM "user_mrg"
                WHERE "user_mrg".key = "user".key)
            """)

        print 'patient...'
        conn.execute("""
            UPDATE "patient"
            SET mrg_id = (
                SELECT id
                FROM "patient_mrg"
                WHERE "patient".our = "patient_mrg".our)
            """)

        print 'partner...'
        conn.execute("""
            INSERT INTO "partner" (
                mrg_id, zid,
                patient_id, enrolled_patient_id,
                report_date,
                create_date, modify_date, revision,
                create_user_id, modify_user_id)
            SELECT
                id, zid,
                (SELECT id FROM "patient" WHERE mrg_id = patient_id),
                (SELECT id FROM "patient" WHERE mrg_id = enrolled_patient_id),
                report_date,
                create_date, modify_date, revision,
                (SELECT id FROM "user" WHERE mrg_id = create_user_id),
                (SELECT id FROM "user" WHERE mrg_id = modify_user_id)
            FROM "partner_mrg"
            """)


        print 'schema...'
        conn.execute("""
            INSERT INTO "schema" (
                mrg_id, name, title, description,
                storage, publish_date, state, is_inline,
                create_date, modify_date, revision,
                create_user_id, modify_user_id)
            SELECT
                id, name, title, description,
                storage, publish_date, state, is_inline,
                create_date, modify_date, revision,
                (SELECT id FROM "user" WHERE mrg_id = create_user_id),
                (SELECT id FROM "user" WHERE mrg_id = modify_user_id)
            FROM "schema_mrg"
            """)

        print 'attribute...'
        conn.execute("""
            INSERT INTO "attribute" (
                mrg_id, name, title, description,
                type, is_private, is_collection, is_required, checksum, "order",
                schema_id,
                object_schema_id,
                create_date, modify_date, revision,
                create_user_id, modify_user_id)
            SELECT
                id, name, title, description,
                type, TRUE, is_collection, is_required, checksum, "order",
                (SELECT id FROM "schema" WHERE mrg_id = schema_id),
                (SELECT id FROM "schema" WHERE mrg_id = object_schema_id),
                create_date, modify_date, revision,
                (SELECT id FROM "user" WHERE mrg_id = create_user_id),
                (SELECT id FROM "user" WHERE mrg_id = modify_user_id)
            FROM "attribute_mrg"
            """)

        print 'choice...'
        conn.execute("""
            INSERT INTO "choice" (
                mrg_id, name, title, description,
                value, "order",
                attribute_id,
                create_date, modify_date, revision,
                create_user_id, modify_user_id)
            SELECT
                id, name, title, description,
                value, "order",
                (SELECT id FROM "attribute" WHERE mrg_id = attribute_id),
                create_date, modify_date, revision,
                (SELECT id FROM "user" WHERE mrg_id = create_user_id),
                (SELECT id FROM "user" WHERE mrg_id = modify_user_id)
            FROM "choice_mrg"
            """)

        print 'entity...'
        conn.execute("""
            INSERT INTO "entity" (
                mrg_id, name, title, description, state, collect_date,
                schema_id,
                create_date, modify_date, revision,
                create_user_id, modify_user_id)
            SELECT
                id, name, title, description, state, collect_date,
                (SELECT id FROM "schema" WHERE mrg_id = schema_id),
                create_date, modify_date, revision,
                (SELECT id FROM "user" WHERE mrg_id = create_user_id),
                (SELECT id FROM "user" WHERE mrg_id = modify_user_id)
            FROM "entity_mrg"
            """)

        for value in ('datetime', 'integer', 'blob', 'text', 'decimal', 'string', 'object'):
            print value + '...'

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
                    create_user_id, modify_user_id)
                SELECT
                    id,
                    (SELECT id FROM "entity" WHERE mrg_id = entity_id),
                    (SELECT id FROM "attribute" WHERE mrg_id = attribute_id),
                    (SELECT id FROM "choice" WHERE mrg_id = choice_id),
                    {1},
                    create_date, modify_date, revision,
                    (SELECT id FROM "user" WHERE mrg_id = create_user_id),
                    (SELECT id FROM "user" WHERE mrg_id = modify_user_id)
                FROM "{0}_mrg"
                """.format(value, value_getter))

        print 'context...'
        for row in conn.execute('SELECT DISTINCT external FROM context_mrg'):
            conn.execute("""
                INSERT INTO context (
                    mrg_id,
                    entity_id,
                    external,
                    key,
                    create_date, modify_date, revision,
                    create_user_id, modify_user_id)
                SELECT
                    id,
                    (SELECT id FROM "entity" WHERE mrg_id = entity_id),
                    external,
                    (SELECT id FROM "{0}" WHERE mrg_id = key),
                    create_date, modify_date, revision,
                    (SELECT id FROM "user" WHERE mrg_id = create_user_id),
                    (SELECT id FROM "user" WHERE mrg_id = modify_user_id)
                FROM "context_mrg"
                WHERE external = '{0}'
                AND EXISTS( SELECT 1 FROM "{0}" WHERE mrg_id = key )
                """.format(row['external']))

        for table in TABLES:
            conn.execute('ALTER TABLE "{0}" DROP COLUMN mrg_id'.format(table))

def main():
    args = cli.parse_args()

    cleanup(args.phi)
    cleanup(args.fia)

    prepare(args.phi)
    migrate(args.phi, args.fia)
    cleanup(args.phi)

    integrate(args.fia)
    cleanup(args.fia)


if __name__ == '__main__':
    main()

