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
FILE_TRIGGERS = os.path.join(HERE, 'triggers', 'setup.py')
FILE_ALEMBIC = os.path.join(HERE, '..', 'alembic.ini')


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

    check_call(['python', FILE_TRIGGERS, phi, fia, target], shell=True)


if __name__ == '__main__':
    main(sys.argv)
