"""
Command-line interface for exporting data
"""

import argparse
import sys

from six.moves import map, filter
from sqlalchemy import create_engine
from tabulate import tabulate

from occams.clinical import Session, reports


def parse_args(argv=sys.argv):
    parser = argparse.ArgumentParser(description='Generate export data files.')

    conn_group = parser.add_argument_group('Connection options')
    conn_group.add_argument(
        '--db',
        metavar='DBURI',
        dest='db',
        required=True,
        help='Database URL')

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

    Session.configure(bind=create_engine(args.db))

    if args.list:
        print_list(args)
    else:
        make_export(args)

    sys.exit(1)


def print_list(args):
    """
    Prints tabulated list of available data files
    """

    def star(condition):
        return '*' if condition else ''

    def format(row):
        return star(row.has_private), star(row.has_rand), row.name, row.title

    header = ['priv', 'rand', 'name', 'title']
    rows = iter(map(format, reports.list_all()))
    print(tabulate(rows, header, tablefmt='simple'))


def make_export(args):
    """
    Generates the export data files
    """

    if not (args.all or args.all_public or args.all_rand or args.names):
        print('You must specifiy something to export!')
        return

    def is_valid_target(item):
        if args.all:
            return True
        elif args.all_private:
            return item.has_private
        elif args.all_rand:
            return item.has_rand
        elif args.names:
            return item.name in args.names

    items = iter(filter(is_valid_target, reports.list_all()))
    reports.write_reports(args.dir, items)


if __name__ == '__main__':
    main()
