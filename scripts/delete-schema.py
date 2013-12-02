"""
Utility to permanently delete schemata.

The current system does not have a GUI for this and it is a much needed feature.
"""

import argparse
import datetime

from sqlalchemy import create_engine, orm

from occams.datastore import model


Session = orm.scoped_session(orm.sessionmaker(
        user=None,
        class_=model.DataStoreSession))


def schema_arg(str):
    try:
        return int(str)
    except ValueError:
        name, date = str.split('@')
        return name, datetime.datetime.strptime(date, '%Y-%m-%d').date()


cli_parser = argparse.ArgumentParser(description='Delete a schema')

cli_parser.add_argument(
    '-b','--blame',
    metavar='USER',
    help='The user to blame')

cli_parser.add_argument(
    '-u','--uri',
    metavar='URI',
    help='A database URI (vendor://user:pw@host/db')

cli_parser.add_argument(
    '-f', '--force',
    action='store_true',
    help='Force delete without promp')

cli_parser.add_argument(
    'schemata',
    nargs='+',
    type=schema_arg,
    metavar='SCHEMA',
    help='The schemata to delete (Format: id or name@yyyy-mm-dd)')


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

    Session.configure(
        user=lambda: args.blame,
        bind=create_engine(args.uri))

    print ('Deleting the following schemata:')

    for id_or_name in args.schemata:
        try:
            schema = get_schema(Session, id_or_name)
            msg = '{schema.id} {schema.name}, {schema.title}, {schema.state}, {schema.publish_date}'
            print msg.format(schema=schema)
        except orm.exc.NoResultFound:
            print ('FATAL: Not found: {0}'.format(id_or_name))
            continue

        count = Session.query(model.Entity).filter_by(schema=schema).count()

        if count > 0:
            msg = 'WARNING: {0} has {1} entries!!! Aborting...'
            print(msg.format(schema.name, count))
            Session.rollback()
            exit()

        Session.delete(schema)

    if args.force or raw_input('\nContinue? (y/n): ').lower().startswith('y'):
        print('Saving changes')
        Session.commit()
    else:
        print('Aborting...')
        Session.rollback()


if __name__ == '__main__':
    main()

