"""
Command-line interface for exporting data
"""

import argparse
from itertools import chain
import os
import sys

from pyramid.paster import get_appsettings
from six import itervalues
from six.moves import map, filter
from sqlalchemy import create_engine, engine_from_config
from tabulate import tabulate

from .. import Session, exports


def parse_args(argv=sys.argv):
    parser = argparse.ArgumentParser(description='Generate export data files.')

    conn_group = parser.add_argument_group('Connection options')
    conn_group.add_argument(
        '--db',
        metavar='DBURI',
        dest='db',
        help='Database URL')

    conn_group.add_argument(
        '-c', '--config',
        metavar='INI',
        dest='config',
        help='Application INI file')

    main_group = parser.add_argument_group('General Options')
    main_group.add_argument(
        '-l', '--list',
        action='store_true',
        help='List available data files to export, then exit.')
    main_group.add_argument(
        '--all-rand',
        action='store_true',
        help='Only export files with randomization data')
    main_group.add_argument(
        '--all-private',
        action='store_true',
        help='Only export files with private')
    main_group.add_argument(
        '--all-public',
        action='store_true',
        help='Only export files with no private data')
    main_group.add_argument(
        '--all',
        action='store_true',
        help='Export all data files')
    main_group.add_argument(
        'names',
        metavar='NAME',
        nargs='*',
        help='Only export specified data files.')

    export_group = parser.add_argument_group('Export Options')
    export_group.add_argument(
        '--use-choice-labels',
        dest='use_choice_labels',
        action='store_true',
        help='Use choice labels as value instead of codes')
    export_group.add_argument(
        '--expand-collections',
        dest='expand_collections',
        action='store_true',
        help='Expands multi-selects to one row per '
             'possible selection')
    export_group.add_argument(
        '--ignore-private',
        dest='ignore_private',
        action='store_true',
        help='De-identifies private data.')
    export_group.add_argument(
        '--dir',
        metavar='PATH',
        dest='dir',
        help='Output directory')

    return parser.parse_args(argv)


def main(argv=sys.argv):
    args = parse_args(argv[1:])

    if args.list:
        print_list(args)
    else:
        make_export(args)


def print_list(args):
    """
    Prints tabulated list of available data files
    """

    def star(condition):
        return '*' if condition else ''

    def format(row):
        return star(row.has_private), star(row.has_rand), row.name, row.title

    header = ['priv', 'rand', 'name', 'title']
    rows = iter(map(format, itervalues(exports.list_all())))
    print(tabulate(rows, header, tablefmt='simple'))


def make_export(args):
    """
    Generates the export data files
    """
    if args.config:
        engine = engine_from_config(get_appsettings(args.config), 'app.db.')
    elif args.db:
        engine = create_engine(args.db)
    else:
        sys.exit('You must specify either a connection or app configuration')

    Session.configure(bind=engine)

    if not (args.all
            or args.all_public
            or args.all_private
            or args.all_rand
            or args.names):
        sys.exit('You must specifiy something to export!')

    def is_valid_target(item):
        return (
            args.all
            or (args.all_private and item.has_private and not item.has_rand)
            or (args.all_public and not item.has_private and not item.has_rand)
            or (args.all_rand and item.has_rand)
            or (args.names and item.name in args.names))

    exportables = exports.list_all()

    for plan in iter(filter(is_valid_target, itervalues(exportables))):
        with open(os.path.join(args.dir, plan.file_name), 'w+b') as fp:
            exports.write_data(fp, plan.data(
                use_choice_labels=args.use_choice_labels,
                expand_collections=args.expand_collections))

    with open(os.path.join(args.dir, exports.codebook.FILE_NAME), 'w+b') as fp:
        codebooks = [p.codebook() for p in itervalues(exportables)]
        exports.write_codebook(fp, chain.from_iterable(codebooks))
