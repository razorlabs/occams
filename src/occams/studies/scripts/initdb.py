import argparse
import sys

from alembic.config import Config
from alembic import command
from pyramid.paster import get_appsettings, setup_logging
from sqlalchemy import engine_from_config, create_engine

from occams.datastore import models as datastore

from .. import models

parser = argparse.ArgumentParser(description='Initialize database')

# Either one works
parser.add_argument('-c', '--config',  metavar='INI')
parser.add_argument('-d', '--db', type=create_engine, metavar='URL')


def main(argv=sys.argv):
    args = parser.parse_args(argv[1:])

    if args.config:
        setup_logging(args.config)
        settings = get_appsettings(args.config)
        engine = engine_from_config(settings, 'app.db.')
    elif args.db:
        engine = args.db
    else:
        print(u'Must specify either CONFIG or URL')
        parser.print_help()
        exit(0)

    with engine.begin() as connection:
        datastore.DataStoreModel.metadata.create_all(connection)
        models.Base.metadata.create_all(connection)

    # "stamp" the new tables (so upgrades don't get confused)
    alembic_cfg = Config(args.config)
    # XXX: There is no way to stamp in transaction until alembic # 0.7.5
    # alembic_cfg.attributes['connection'] = connection
    command.stamp(alembic_cfg, 'head')
