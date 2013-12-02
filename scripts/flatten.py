"""
Utility to flatten a form and it's data.
"""

import argparse
from copy import deepcopy
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


cli_parser = argparse.ArgumentParser(description='Flatten a schema and it\'s associated entities')

cli_parser.add_argument(
    '-b','--blame',
    metavar='USER',
    help='The user to blame in the target database')

cli_parser.add_argument(
    '-u', '--uri',
    metavar='URI',
    help='Database URI (vendor://user:pw@host/db')

cli_parser.add_argument(
    'schema',
    type=schema_arg,
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

    Session.configure(
        user=lambda: args.blame,
        bind=create_engine(args.uri))

    try:
        schema = get_schema(Session, args.schema)
    except orm.exc.NoResultFound:
        print ('WARNING: Not found: {0}'.format(id_or_name))
        exit()

    msg = ('Flattening the following shema and it\'s data: '
            '{schema.name}, {schema.title}, {schema.state}, {schema.publish_date}')
    print(msg.format(schema=schema))

    object_query =  (
        Session.query(model.ValueObject)
        .join(model.Entity, (model.Entity.id == model.ValueObject.entity_id))
        .filter(model.Entity.schema == schema))

    for value_object in object_query:
        for ValueClass in (model.ValueString, model.ValueInteger, model.ValueDatetime, model.ValueDecimal, model.ValueBlob, model.ValueText):
            value_query = (
                Session.query(ValueClass)
                .filter(ValueClass.entity_id == value_object._value)
                .update({'entity_id': value_object.entity_id}))
        Session.delete(value_object)

    subschema_ids = [s.object_schema_id for s in schema.values() if s.type == 'object']

    (Session.query(model.Attribute)
        .filter(model.Attribute.schema_id == schema.id)
        .filter(model.Attribute.type == 'object')
        .update({'order': model.Attribute.order + 1000000}, False))

    (Session.query(model.Attribute)
        .filter(model.Attribute.schema_id.in_(subschema_ids))
        .update({'schema_id': schema.id}, False))

    (Session.query(model.Attribute)
        .filter(model.Attribute.schema_id == schema.id)
        .filter(model.Attribute.type == 'object')
        .delete())

    Session.commit()


if __name__ == '__main__':
    main()

