"""
Comprehensive upgrade from A-Z
"""

import argparse
import os
import sys
from subprocess import check_call

from sqlalchemy.engine.url import URL


HERE = os.path.abspath(os.path.dirname(__file__))

FILE_CODES = os.path.join(HERE, 'scripts', 'choice2codes.sql')
FILE_VARS = os.path.join(HERE, 'scripts', 'varnames.sql')
FILE_LABFIX = os.path.join(HERE, 'scripts', 'lab_fix.sql')
FILE_MERGE = os.path.join(HERE, 'scripts', 'mergedb.py')
FILE_TRIGGERS = os.path.join(HERE, 'triggers', 'setup.py')
FILE_ALEMBIC = os.path.join(HERE, '..', 'alembic.ini')


cli = argparse.ArgumentParser(description='Fully upgrades the database')
cli.add_argument('-U', dest='user', metavar='USER:PW')
cli.add_argument('-O', dest='owner', metavar='OWNER:PW')
cli.add_argument('--phi', metavar='DB', help='PHI database')
cli.add_argument('--fia', metavar='DB', help='FIA database')
cli.add_argument('--target', metavar='DB', help='Merged database')


def main(argv):
    args = cli.parse_args(argv[1:])

    uid, upw = args.user.split(':')
    oid, opw = args.owner.split(':')

    for db in (args.fia, args.phi):
        check_call(
            '/usr/pgsql-9.3/bin/psql -f {0} "user={user} password={pw} dbname={db}"'
            .format(FILE_CODES, user=oid, pw=opw, db=db),
            shell=True)
        check_call(
            '/usr/pgsql-9.3/bin/psql -f {0} "user={user} password={pw} dbname={db}"'
            .format(FILE_VARS, user=oid, pw=opw, db=db),
            shell=True)
        check_call(
            '/usr/pgsql-9.3/bin/psql -f {0} "user={user} password={pw} dbname={db}"'
            .format(FILE_LABFIX, user=oid, pw=opw, db=db),
            shell=True)

    # Merge the database
    check_call(
        'python {0} -U {user} \
                    -O {owner} \
                    --phi={phi} \
                    --fia={fia} \
                    --target={target}'
        .format(FILE_MERGE, **vars(args)),
        shell=True)

    # Upgrade the database
    check_call('alembic -c {0} -x db="{target}" upgrade head'
               .format(FILE_ALEMBIC, target=str(URL('postgresql',
                                                    username=oid,
                                                    password=opw,
                                                    database=args.target))),
               shell=True)

    # Install triggers
    check_call(
        'python {0} -U {user} \
                    -O {owner} \
                    --phi={phi} \
                    --fia={fia} \
                    --target={target}'
        .format(FILE_TRIGGERS, **vars(args)),
        shell=True)

if __name__ == '__main__':
    main(sys.argv)
