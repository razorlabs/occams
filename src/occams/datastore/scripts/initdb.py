import argparse
import sys

from sqlalchemy import engine_from_config, create_engine

from occams.datastore import models

parser = argparse.ArgumentParser(description='Initialize database')

# Either one works
parser.add_argument('-c', '--config',  metavar='INI')
parser.add_argument('-d', '--db', type=create_engine, metavar='URL')


def main(argv=sys.argv):
    args = parser.parse_args(argv[1:])

    if args.config:
        try:
            from pyramid.paster import get_appsettings, setup_logging
        except ImportError:
            raise Exception(u'This option may only be used if using Pyramid')
        else:
            config_uri = args.config_url
            setup_logging(config_uri)
            settings = get_appsettings(config_uri)
            engine = engine_from_config(settings, 'app.db.')

    elif args.db:
        import logging
        # Configure the logger if not already done so by a wrapper application
        sa_logger = logging.getLogger('sqlalchemy.engine')
        if not sa_logger.handlers:
            logging.basicConfig()
            sa_logger.setLevel(logging.INFO)
        engine = args.db

    else:
        print(u'Must specify either CONFIG or URL')
        parser.print_help()
        exit(0)

    models.DataStoreModel.metadata.create_all(engine)
