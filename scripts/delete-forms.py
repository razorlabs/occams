"""
Utility to remove forms.
"""

import argparse
import datetime

from sqlalchemy import create_engine, orm

from occams.datastore import model


Session = orm.scoped_session(orm.sessionmaker(
        user=None,
        class_=model.DataStoreSession))


def form_arg(str):
    name, publish_date = str.split('@')
    return name, datetime.date.strftime('%Y-%m-%d', publish_date)


cli_parser = argparse.ArgumentParser(description='Delete a form')

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
    'forms',
    nargs='+',
    type=lambda s: s.split('@'),
    metavar='FORM',
    help='The form(s) to delete (Format: name@yyyy-mm-dd)')


def main():
    args = cli_parser.parse_args()

    Session.configure(
        user=lambda: args.blame,
        bind=create_engine(args.uri))

    print ('Deleting the following forms:')

    for name, date in args.forms:
        try:
            schema = (
                Session.query(model.Schema)
                .filter_by(name=name, publish_date=date)
                .one())
            msg = '{schema.name}, {schema.title}, {schema.state}, {schema.publish_date}'
            print msg.format(schema=schema)
        except orm.exc.NoResultFound:
            print ('FATAL: Not found: {0} {1}'.format(name, date))
            continue

        count = Session.query(model.Entity).filter_by(schema=schema).count()

        if count > 0:
            msg = 'FATAL: {0} has {1} entries!!! Aborting...'
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

