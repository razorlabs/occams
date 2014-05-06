"""
Installs triggers


Some tables define a ext_TABLE_id functions so that tables that have references
can properly find the referenced table in the remote system.
These functions cannot be used in the actual update triggers because the
data will have already changed by the time the function is useful.

Uses old_db/old_id semantics to reconcile both databases. In cases where the
data exists in both databases (such as user/patient/context), data is aligned
by their unique key

Merge scenarios:
  * Data exists in both databases and, thus, can have mismatching primary
    keys (user, all studies, partner)
      * Use unique keys (i.e, name, or zid)
  * Data is poluated in both databases, but mutually exclusive
    (datastore phi/fia)
      *  Use old_db/old_id
  * Data is populated in only one database (calllog, lab)
      * Use old_db/old_id

"""
import argparse
import os
import sys

import psycopg2
from sqlalchemy.engine.url import URL

HERE = os.path.abspath(os.path.dirname(__file__))

cli = argparse.ArgumentParser(description='Sets up triggers')
cli.add_argument('-U', dest='user', metavar='USER:PW')
cli.add_argument('-O', dest='owner', metavar='OWNER:PW')
cli.add_argument('--phi', metavar='DB', help='PHI database')
cli.add_argument('--fia', metavar='DB', help='FIA database')
cli.add_argument('--target', metavar='DB', help='Merged database')


def main(argv):
    args = cli.parse_args(argv[1:])

    uid, upw = args.user.split(':')
    oid, opw = args.owner.split(':')

    phi = URL('postgresql', username=oid, password=opw, database=args.phi)
    fia = URL('postgresql', username=oid, password=opw, database=args.fia)
    target = URL('postgresql', username=oid, password=opw, database=args.target)

    # Install triggers in old database to push data to the new database
    install(uid, upw, fia, target)
    install(uid, upw, phi, target)


def install(suid, supw, from_url, to_url):

    conn = psycopg2.connect(user=suid,
                            password=supw,
                            host=from_url.host,
                            port=from_url.port,
                            database=from_url.database)
    cursor = conn.cursor()

    cursor.execute("""
        DROP EXTENSION IF EXISTS postgres_fdw CASCADE;
        CREATE EXTENSION postgres_fdw;

        DROP EXTENSION IF EXISTS dblink CASCADE;
        CREATE EXTENSION dblink;

        CREATE SERVER trigger_target
        FOREIGN DATA WRAPPER postgres_fdw
        OPTIONS (dbname '{database}');

        CREATE USER MAPPING FOR {username}
        SERVER trigger_target
        OPTIONS(user '{username}', password '{password}');

        GRANT USAGE ON FOREIGN SERVER trigger_target TO {username};
    """.format(**to_url.translate_connect_args()))

    products = ('studies', 'datastore', 'lab', 'partner')

    if 'cctg' in from_url.database:
        products += ('calllog',)

    for product in products:
        product_dir = os.path.join(HERE, product)
        for file in os.listdir(product_dir):
            with open(os.path.join(product_dir, file)) as fp:
                cursor.execute(fp.read())
        cursor.execute("""
            GRANT SELECT, INSERT, UPDATE, DELETE
            ON ALL TABLES IN SCHEMA public
            TO {username};

            GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO {username};
        """.format(**from_url.translate_connect_args()))

    if 'phi' in from_url.database:
        # Ignore these on the PHI side since it will gridlock the remote
        cursor.execute("""
            DROP TRIGGER patient_mirror ON "patient";
            DROP TRIGGER user_mirror ON "user";
        """)

    conn.commit()
    cursor.close()
    conn.close()


if __name__ == '__main__':
    main(sys.argv)
