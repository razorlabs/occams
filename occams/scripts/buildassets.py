"""
Utility script for building OCCAMS assets offline.

Currently request time takes about 30 seconds for the first access
because Pyramid needs to compile all the templates and static assets.
"""
import argparse
import sys

from pyramid.paster import bootstrap
import webassets.script

parser = argparse.ArgumentParser(description='Builds application assets')
parser.add_argument(
    '-c', '--config',  metavar='INI',
    help='Installs using an existing application INI')


def main(argv=sys.argv):
    args = parser.parse_args(argv[1:])

    if not args.config:
        print(u'Must specify a CONFIG')
        parser.print_help()
        exit(0)

    app_env = bootstrap(args.config)
    assets_env = app_env['request'].webassets_env
    webassets.script.main(['build'], assets_env)
