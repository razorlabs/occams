import argparse
import logging
import sys

from alembic.config import Config
from alembic import command
from pyramid.paster import get_appsettings, setup_logging
from sqlalchemy import engine_from_config, create_engine

from occams_datastore import models as datastore

from .. import models


parser = argparse.ArgumentParser(description='Initialize database')
parser.add_argument(
    '-c', '--config',  metavar='INI',
    help='Installs using an existing application INI')
parser.add_argument(
    '-d', '--db', metavar='URL',
    help='Installs to target URL, useful testing a database')


def main(argv=sys.argv):
    args = parser.parse_args(argv[1:])

    if args.config:
        # Parse the config URI in case there's a specified section
        filename, _, app = args.config.partition('#')
        setup_logging(filename)
        settings = get_appsettings(args.config)
        engine = engine_from_config(settings, 'occams.db.')
        alembic_cfg = Config(filename)

    elif args.db:
        logging.basicConfig()
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
        engine = create_engine(args.db)

    else:
        print(u'Must specify either CONFIG or URL')
        parser.print_help()
        exit(0)

    with engine.begin() as connection:
        datastore.DataStoreModel.metadata.create_all(connection)
        models.Base.metadata.create_all(connection)

    if args.config:
        # "stamp" the new tables (so upgrades don't get confused)
        # XXX: There is no way to stamp inside transaction until alembic 0.7.5
        # alembic_cfg.attributes['connection'] = connection
        command.stamp(alembic_cfg, 'head')
    else:
        print('Cannot stamp until almebic 0.7.5, deal with it...')
