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
from importlib import import_module

from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine
from pyramid.paster import setup_logging, get_appsettings
from pyramid.settings import aslist


parser = argparse.ArgumentParser(description='Initialize database')
parser.add_argument(
    'config',
    metavar='INI',
    help='Installs using an existing application INI')


def main(argv=sys.argv):
    args = parser.parse_args(argv[1:])

    setup_logging(args.config)
    app_settings = get_appsettings(args.config)
    alembic_cfg = Config(args.config)

    blame = alembic_cfg.get_main_option('blame')
    engine = create_engine(alembic_cfg.get_main_option('sqlalchemy.url'))
    apps = aslist(app_settings['occams.apps'])
    errors = []

    assert blame, 'Need to blame someone!'

    with engine.begin() as connection:
        connection.info['blame'] = blame

        for app in apps:
            try:
                module = import_module(app)
            except ImportError:
                errors.append('{}: Unable to import'.format(app))
                continue
            else:
                if hasattr(module, 'initdb'):
                    module.initdb(connection)
                else:
                    errors.append('{}: Does not have "initdb"'.format(app))

        for error in errors:
            print(error)

        alembic_cfg.attributes['connection'] = connection
        command.stamp(alembic_cfg, 'head')
