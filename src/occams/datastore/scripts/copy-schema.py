"""
Utility to move a form from one server to another.

The current system does not have a GUI for this and
it is a much needed feature.
"""

import argparse
import datetime

from sqlalchemy import create_engine, orm

from .. import models
from ..models.events import register


SourceSession = orm.scoped_session(orm.sessionmaker())
register(SourceSession)

TargetSession = orm.scoped_session(orm.sessionmaker())
register(TargetSession)


def schema_arg(str):
    try:
        return int(str)
    except ValueError:
        name, date = str.split('@')
        return name, datetime.datetime.strptime(date, '%Y-%m-%d').date()


cli_parser = argparse.ArgumentParser(description='Move a schema')

cli_parser.add_argument(
    '-b', '--blame',
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


def main():
    args = cli_parser.parse_args()

    SourceSession.configure(
        bind=create_engine(args.source),
        info={'user': args.blame})

    TargetSession.configure(
        bind=create_engine(args.target),
        info={'user': args.blame})

    print ('Moving the following forms:')

    for name_or_id in args.schemata:
        try:
            query = SourceSession.query(models.Schema)
            if isinstance(name_or_id, int):
                query = query.filter_by(id=name_or_id)
            else:
                name, date = name_or_id
                query = query.filter_by(name=name, publish_date=date)
            schema = query.one()
            msg = ('{schema.name}, '
                   '{schema.title}, '
                   '{schema.state}, '
                   '{schema.publish_date}')
            print(msg.format(schema=schema))
        except orm.exc.NoResultFound:
            print ('WARNING: Not found: {0}'.format(name_or_id))
            continue
        json_data = schema.to_json()
        TargetSession.add(models.Schema.from_json(json_data))
        TargetSession.flush()

    TargetSession.commit()


if __name__ == '__main__':
    main()
