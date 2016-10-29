"""
This script will install databases listed in the almebic section
of the configuration file.

Please ensure that this user has different privilidges than the
application user. The initdb user should ideally have "create" priviliges
and the application user should ideally only have insert/update/delete/select
depending on the classification of the table.

"""

import argparse
import sys

from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine
from pyramid.paster import setup_logging

from ..models.meta import Base


parser = argparse.ArgumentParser(description='Initialize database')
parser.add_argument(
    'config',
    metavar='INI',
    help='Installs using an existing application INI')


def main(argv=sys.argv):
    args = parser.parse_args(argv[1:])

    setup_logging(args.config)
    alembic_cfg = Config(args.config)

    blame = alembic_cfg.get_main_option('blame')
    engine = create_engine(alembic_cfg.get_main_option('sqlalchemy.url'))

    assert blame, 'Need to blame someone!'

    with engine.begin() as connection:
        connection.info['blame'] = blame
        Base.metadata.create_all(connection)
        alembic_cfg.attributes['connection'] = connection
        command.stamp(alembic_cfg, 'heads')
