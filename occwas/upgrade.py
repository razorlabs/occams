"""
Comprehensive upgrade from A-Z
"""
import argparse
import os
from subprocess import check_call
import sys

from sqlalchemy.engine.url import make_url

HERE = os.path.abspath(os.path.dirname(__file__))

FILE_CODES = os.path.join(HERE, 'scripts', 'choice2codes.sql')
FILE_MERGE = os.path.join(HERE, 'scripts', 'mergedb.py')
FILE_ALEMBIC = os.path.join(HERE, '..', 'alembic.ini')

PRODUCTS = ('clinical', 'datastore', 'lab', 'partner')
CCTG_PRODUCTS = PRODUCTS + ('calllog',)


cli = argparse.ArgumentParser(description='Fully upgrades the database')
cli.add_argument('phi', metavar='PHI', type=make_url)
cli.add_argument('fia', metavar='FIA', type=make_url)
cli.add_argument('target', metavar='TARGET', type=make_url)


def main(argv):
    args = cli.parse_args(argv[1:])
    (fia, phi, target) = (args.fia, args.phi, args.target)

    # Switch to codes
    for url in (fia, phi):
        check_call(['psql', '-U', url.username, '-f', FILE_CODES], shell=True)

    # Merge the database
    check_call(['python', FILE_MERGE, phi, fia, target], shell=True)

    # Upgrade the database
    check_call(['alembic', '-c', FILE_ALEMBIC, '-x', 'db=' + target],
               shell=True)

    # Install triggers in old database to push data to the new database
    for url in (fia, phi):
        check_call('psql -U {0} -f {1} {2}'.format(
                   'postgres',
                   os.path.join(HERE, 'triggers', 'setup.sql'),
                   url.database),
                   shell=True)
        for product in (PRODUCTS if 'cctg' not in url.database else CCTG_PRODUCTS):
            product_dir = os.path.join(HERE, 'triggers', product)
            for file in os.listdir(product_dir):
                check_call('psql -U {0} -f {1} {2}'.format(
                           'postgres',
                           os.path.join(product_dir, file),
                           url.database),
                           shell=True)

if __name__ == '__main__':
    main(sys.argv)
