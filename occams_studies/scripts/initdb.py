import argparse
import sys

from alembic.config import Config
from alembic import command
from pyramid.paster import get_appsettings, setup_logging
from sqlalchemy import engine_from_config
import transaction

from occams_datastore import models as datastore

from .. import models, Session


parser = argparse.ArgumentParser(description='Initialize database')
parser.add_argument(
    'config',
    metavar='INI',
    help='Installs using an existing application INI')


def main(argv=sys.argv):
    args = parser.parse_args(argv[1:])

    # Parse the config URI in case there's a specified section
    filename, _, app = args.config.partition('#')
    setup_logging(filename)
    settings = get_appsettings(args.config)
    engine = engine_from_config(settings, 'occams.db.')
    alembic_cfg = Config(args.config)

    with engine.begin() as connection:
        datastore.DataStoreModel.metadata.create_all(connection)
        models.Base.metadata.create_all(connection)

        alembic_cfg.attributes['connection'] = connection
        command.stamp(alembic_cfg, 'head')

    Session.configure(bind=engine)

    with transaction.manager:

        blame = models.User(key=alembic_cfg.get_main_option('blame'))
        Session.add(blame)
        Session.flush()

        Session.info['blame'] = blame

        Session.add_all([
            models.State(name=u'pending-entry', title=u'Pending Entry'),
            models.State(name=u'in-pogress', title=u'In Progress'),
            models.State(name=u'pending-review', title=u'Pending Review'),
            models.State(name=u'pending-correction', title=u'Pending Correction'),
            models.State(name=u'complete', title=u'Complete'),
        ])
