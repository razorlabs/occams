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
    keys (user, all clinical, partner)
      * Use unique keys (i.e, name, or zid)
  * Data is poluated in both databases, but mutually exclusive
    (datastore phi/fia)
      *  Use old_db/old_id
  * Data is populated in only one database (calllog, lab)
      * Use old_db/old_id

"""
import argparse
import os
from subprocess import check_call
import sys

from sqlalchemy.engine.url import make_url

HERE = os.path.abspath(os.path.dirname(__file__))


PRODUCTS = ('clinical', 'datastore', 'lab', 'partner')
CCTG_PRODUCTS = PRODUCTS + ('calllog',)


cli = argparse.ArgumentParser(description='Fully upgrades the database')
cli.add_argument('phi', metavar='PHI', type=make_url)
cli.add_argument('fia', metavar='FIA', type=make_url)
cli.add_argument('target', metavar='TARGET', type=make_url)


def main(argv):
    args = cli.parse_args(argv[1:])
    (fia, phi, target) = (args.fia, args.phi, args.target)

    # Install triggers in old database to push data to the new database
    for url in (fia, phi):
        check_call('psql -U {0} -d {1} -c "DROP EXTENSION IF EXISTS postgres_fdw CASCADE"'
                   .format('postgres', url.database),
                   shell=True)

        check_call('psql -U {0} -d {1} -c "CREATE EXTENSION postgres_fdw"'
                   .format('postgres', url.database),
                   shell=True)
        check_call('psql -U {0} -d {1} -c "CREATE SERVER trigger_target FOREIGN DATA WRAPPER postgres_fdw OPTIONS (dbname \'{2}\')"'
                   .format('postgres', url.database, target.database),
                   shell=True)
        check_call('psql -U {0} -d {1} -c "CREATE USER MAPPING FOR USER SERVER trigger_target"'
                   .format('postgres', url.database),
                   shell=True)

        for product in (PRODUCTS if 'cctg' not in url.database else CCTG_PRODUCTS):
            product_dir = os.path.join(HERE, product)
            for file in os.listdir(product_dir):
                check_call('psql -U {0} -f {1} {2}'.format(
                           'postgres',
                           os.path.join(product_dir, file),
                           url.database),
                           shell=True)


if __name__ == '__main__':
    main(sys.argv)
