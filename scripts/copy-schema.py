"""
Utility to move a form from one server to another.

The current system does not have a GUI for this and it is a much needed feature.
"""

import argparse
from copy import deepcopy
import datetime

from sqlalchemy import create_engine, orm

from occams.datastore import model


SourceSession = orm.scoped_session(orm.sessionmaker(
        user=None,
        class_=model.DataStoreSession))


TargetSession = orm.scoped_session(orm.sessionmaker(
        user=None,
        class_=model.DataStoreSession))


def schema_arg(str):
    try:
        return int(str)
    except ValueError:
        name, date = str.split('@')
        return name, datetime.datetime.strptime(date, '%Y-%m-%d').date()


cli_parser = argparse.ArgumentParser(description='Move a schema')

cli_parser.add_argument(
    '-b','--blame',
    metavar='USER',
    help='The user to blame in the target database')

cli_parser.add_argument(
    '-s', '--source',
    metavar='URI',
    help='Source database URI (vendor://user:pw@host/db')

cli_parser.add_argument(
    '-t', '--target',
    metavar='URI',
    help='Target database URI (vendor://user:pw@host/db')

cli_parser.add_argument(
    'schemata',
    type=schema_arg,
    nargs='+',
    metavar='SCHEMA',
    help='The schemata to move (Format: id OR name@yyyy-mm-dd)')


def get_schema(session, id_or_name):
    query = session.query(model.Schema)
    if isinstance(id_or_name, int):
        query = query.filter_by(id=id_or_name)
    else:
        name, date = id_or_name
        query = query.filter_by(name=name, publish_date=date)
    return query.one()


def main():
    args = cli_parser.parse_args()

    SourceSession.configure(
        user=lambda: args.blame,
        bind=create_engine(args.source))

    TargetSession.configure(
        user=lambda: args.blame,
        bind=create_engine(args.target))

    print ('Moving the following forms:')

    for name_or_id in args.schemata:
        try:
            schema = get_schema(SourceSession, name_or_id)
            msg = '{schema.name}, {schema.title}, {schema.state}, {schema.publish_date}'
            print msg.format(schema=schema)
        except orm.exc.NoResultFound:
            print ('WARNING: Not found: {0}'.format(id_or_name))
            continue
        # remove the categories, as they might not exist in the target database
        schema.categories = set()
        schema_copy = deepcopy(schema)
        # don't commit the changes made to the source
        SourceSession.rollback()
        TargetSession.add(schema_copy)
        TargetSession.flush()

    TargetSession.commit()


if __name__ == '__main__':
    main()

