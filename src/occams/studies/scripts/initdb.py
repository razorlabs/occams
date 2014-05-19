import argparse
import sys

from pyramid.paster import get_appsettings, setup_logging
from sqlalchemy import engine_from_config

from .. import models


def parse_args(argv=sys.argv):
    parser = argparse.ArgumentParser(description='Initialize database')
    parser.add_argument('config_uri', metavar='INI')
    return parser.parse_args(argv)


def main(argv=sys.argv):
    args = parse_args(argv[1:])
    config_uri = args.config_url
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'app.db.')
    models.Base.metadata.create_all(engine, checkfirst=True)
