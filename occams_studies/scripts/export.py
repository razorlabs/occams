"""
Command-line interface for exporting data
"""

import argparse
from itertools import chain
import os
import shutil
import sys
import uuid

from pyramid.paster import bootstrap, setup_logging
from six import itervalues
from tabulate import tabulate

from .. import exports


def parse_args(argv=sys.argv):
    parser = argparse.ArgumentParser(description='Generate export data files.')

    conn_group = parser.add_argument_group('Connection options')
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
    # Can't use --ignore-private because default behavior is to de-identify
    # private data. Need an explicit flag to disable that behavior.
    export_group.add_argument(
        '--show-private',
        dest='show_private',
        action='store_true',
        help='De-identifies private data.')
    export_group.add_argument(
        '--dir',
        metavar='PATH',
        dest='dir',
        help='Output directory')
    export_group.add_argument(
        '--atomic',
        action='store_true',
        help='Treat the output path as a symlink')

    return parser.parse_args(argv)


def main(argv=sys.argv):
    args = parse_args(argv[1:])

    setup_logging(args.config)
    env = bootstrap(args.config)

    if args.list:
        print_list(args, env)
    else:
        make_export(args, env)


def print_list(args, env):
    """
    Prints tabulated list of available data files
    """

    def star(condition):
        return '*' if condition else ''

    def format(row):
        return star(row.is_system), star(row.has_private), star(row.has_rand), row.name, row.title  # NOQA

    header = ['sys', 'priv', 'rand', 'name', 'title']
    db_session = env['request'].db_session
    plans = env['registry'].settings['studies.export.plans']
    rows = iter(format(e) for e in itervalues(
        exports.list_all(plans, db_session)))
    print(tabulate(rows, header, tablefmt='simple'))


def make_export(args, env):
    """
    Generates the export data files
    """

    if not (args.all
            or args.all_public
            or args.all_private
            or args.all_rand
            or args.names):
        sys.exit('You must specifiy something to export!')

    db_session = env['request'].db_session
    plans = env['registry'].settings['studies.export.plans']
    exportables = exports.list_all(plans, db_session)

    if args.atomic:
        out_dir = '%s-%s' % (args.dir.rstrip('/'), uuid.uuid4())
        os.makedirs(out_dir)
    else:
        out_dir = args.dir
        if not os.path.exists(args.dir):
            os.makedirs(args.dir)

    for plan in itervalues(exportables):
        if (args.all
                or (args.all_private
                    and plan.has_private
                    and not plan.has_rand)
                or (args.all_public
                    and not plan.has_private
                    and not plan.has_rand)
                or (args.all_rand and plan.has_rand)
                or (args.names and plan.name in args.names)):
            with open(os.path.join(out_dir, plan.file_name), 'w+b') as fp:
                exports.write_data(fp, plan.data(
                    use_choice_labels=args.use_choice_labels,
                    expand_collections=args.expand_collections,
                    ignore_private=not args.show_private))

    with open(os.path.join(out_dir, exports.codebook.FILE_NAME), 'w+b') as fp:
        codebooks = [p.codebook() for p in itervalues(exportables)]
        exports.write_codebook(fp, chain.from_iterable(codebooks))

    if args.atomic:
        old_dir = os.path.realpath(args.dir)
        if os.path.islink(args.dir):
            os.unlink(args.dir)
        os.symlink(os.path.abspath(out_dir), args.dir)
        if not os.path.islink(old_dir):
            shutil.rmtree(old_dir)
