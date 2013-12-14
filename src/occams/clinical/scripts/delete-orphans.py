import argparse
import logging

from sqlalchemy import create_engine
from sqlalchemy import orm

from occams.datastore.model import DataStoreSession
from occams.datastore import model


Logger = logging.getLogger(__name__)

Session = orm.scoped_session(orm.sessionmaker(class_=DataStoreSession))

parser = argparse.ArgumentParser(
    description='Removes orphans from the database')
parser.add_argument('-c', metavar='URI', dest='uri', required=True,
                    help='Database connection string')
parser.add_argument('-u', metavar='BLAME', dest='blame', required=True,
                    help='User to blame')
parser.add_argument('-d', '--dry', dest='dry', action='store_true',
                    help='Dry run')


def main():
    """
    This function returns a Pyramid WSGI application.
    """
    args = parser.parse_args()

    Session.configure(bind=create_engine(args.uri), user=lambda: args.blame)

    query = (
        Session.query(model.Entity)
        .filter(model.Entity.schema.has(is_inline=False))
        .filter(~model.Entity.contexts.any()))

    delete_count = query.count()
    print ('Deleting %d entities...' % delete_count)

    # Use delete since doing a build delete will trigger a different event
    map(Session.delete, iter(query))

    if not args.dry:
        print ('Saving changes')
        Session.commit()
    else:
        print('Changes not saved, disable dry run')


if __name__ == '__main__':
    main()
