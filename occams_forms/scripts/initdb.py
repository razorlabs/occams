import argparse
import sys

from alembic.config import Config
from alembic import command
from pyramid.paster import bootstrap, setup_logging
import transaction

from occams_datastore import models as datastore

from .. import models


parser = argparse.ArgumentParser(description='Initialize database')
parser.add_argument(
    'config',
    metavar='INI',
    help='Installs using an existing application INI')
parser.add_argument(
    '-w', '--workflow',
    action='store_true',
    help='Also installs the workflow states')


def main(argv=sys.argv):
    args = parser.parse_args(argv[1:])

    setup_logging(args.config)
    env = bootstrap(args.config)
    alembic_cfg = Config(args.config)

    db_session = env['request'].db_session

    with transaction.manager:
        datastore.DataStoreModel.metadata.create_all(db_session.bind)

        alembic_cfg.attributes['connection'] = db_session.bind.connect()
        command.stamp(alembic_cfg, 'head')

        if args.workflow:
            blame = models.User(key=alembic_cfg.get_main_option('blame'))
            db_session.add(blame)
            db_session.flush()

            db_session.info['blame'] = blame

            db_session.add_all([
                models.State(name=u'pending-entry', title=u'Pending Entry'),
                models.State(name=u'in-pogress', title=u'In Progress'),
                models.State(name=u'pending-review', title=u'Pending Review'),
                models.State(name=u'pending-correction',
                             title=u'Pending Correction'),
                models.State(name=u'complete', title=u'Complete'),
            ])
