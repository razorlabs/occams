"""
Contains long-running tasks that cannot interrupt the user experience.

Tasks in this module will be run in a separate process so the user
can continue to use the application and download their exports at a
later time.
"""

from collections import defaultdict
from contextlib import closing
import json
import os.path
import tempfile
import zipfile
from pkg_resources import resource_filename

import celery
from redis import StrictRedis

from occams.datastore import model as datastore, reporting

from occams.clinical import models, Session
from occams.clinical.utils.csv import UnicodeWriter


@celery.task
def make_export(export_id):
    """
    Handles generating exports in a separate process.

    Because the export is handled in a different process, this method
    can only accept the id of the entry. This is to avoid race
    conditions,
    (http://docs.celeryproject.org/en/latest/userguide/tasks.html#state)

    All progress will be broadcast to the redis **export** channel with the
    following dictionary:
    ``export_id`` -- the export being processed
    ``owner_user`` -- the user who this export belongs to
    ``count`` -- the current number of files processed
    ``total`` -- the total number of files that will be processed
    ``status`` -- current status of the export

    Parameters:
    ``export_id`` -- export to process

    """
    # Get the export instance attached to this thread
    export = Session.query(models.Export).get(export_id)

    export_dir = resource_filename('occams.clinical', 'exports')
    path = os.path.join(export_dir, '%s.zip' % export.id)

    # Organize the forms so we know which schemata go where
    codebooks = defaultdict(set)
    for schema in export.schemata:
        codebooks[schema.name].add(schema.id)

    redis = StrictRedis()

    redis.hmset(export.id, {
        'export_id': export.id,
        'owner_user': export.owner_user.key,
        'status': export.status,
        'count': 0,
        'total': len(export.schemata) + len(codebooks)})

    with closing(zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED)) as zfp:
        # Generate the data files
        for schema in export.schemata:
            report = reporting.export(schema)
            query = (
                Session.query(report.c.entity_id)
                .add_column(
                    Session.query(models.Patient.pid)
                    .distinct()
                    .join(models.Visit)
                    .join(datastore.Context,
                        (datastore.Context.external == 'visit')
                        & (datastore.Context.key == models.Visit.id))
                    .filter(datastore.Context.entity_id == report.c.entity_id)
                    .correlate(report)
                    .as_scalar()
                    .label('pid'))
                .add_columns(*[c for c in report.columns if c.name != 'entity_id']))

            arcname = '{0}-{1}.csv'.format(schema.name, schema.publish_date)
            arc_query(zfp, arcname, query)
            redis.hincrby(export.id, 'count')
            redis.publish('export', json.dumps(redis.hgetall(export.id)))
            print(', '.join(redis.hmget(export.id, 'count', 'total') + [arcname]))

        # Generate the ecrf codebooks
        for name, ids in codebooks.items():
            arcname = '{0}-codebook.csv'.format(name)
            arc_codebook(zfp, arcname, name, ids)
            redis.hincrby(export.id, 'count')
            redis.publish('export', json.dumps(redis.hgetall(export.id)))
            print(', '.join(redis.hmget(export.id, 'count', 'total') + [arcname]))

    # File has been closed/flushed, it's ready for consumption
    export.status = 'complete'
    Session.commit()
    redis.hset(export.id, 'status', export.status)
    redis.publish('export', json.dumps(redis.hgetall(export.id)))


@celery.task
def cleanup_export(expire_date):
    """
    Cleans up the database of expired exports.

    Parameters:
    ``expire_date`` -- the cut-off date for removal
    """
    raise NotImplementedError


@celery.task
def handle_error(uuid):
    """
    Handles asynchronous errors
    """
    print("Oh snap, there was an error")


def arc_query(zfp, arcname, query):
    """
    Dumps an arbitrary query to a CSV file inside an archive file

    Parameters:
    ``zfp`` -- the zip file pointer
    ``arcname`` -- the name inside the archive
    ``query`` -- the source query

    """
    with tempfile.NamedTemporaryFile() as tfp:
        writer = UnicodeWriter(tfp)
        writer.writerow([d['name'] for d in query.column_descriptions])
        writer.writerows(query)
        tfp.flush() # ensure everything's on disk
        zfp.write(tfp.name, arcname)


def arc_codebook(zfp, arcname, name, ids=None):
    """
    Dumps the ecrf into a CSV codebook file inside an archive file

    Parameters:
    ``zfp`` -- the zip file pointer
    ``arcname`` -- the name inside the archive
    ``name`` -- the ecrf schema name
    ``ids`` -- (optional) the specific ids of the schema

    """
    query = (
        Session.query(datastore.Attribute)
        .join(datastore.Schema)
        .filter(datastore.Schema.name == name)
        .filter(datastore.Schema.id.in_(ids))
        .order_by(
            datastore.Attribute.order,
            datastore.Schema.publish_date))

    with tempfile.NamedTemporaryFile() as tfp:
        writer = UnicodeWriter(tfp)
        writer.writerow([
            'form_name',
            'form_title',
            'form_publish_date',
            'field_name',
            'field_title',
            'field_description',
            'field_is_required',
            'field_is_collection',
            'field_type',
            'field_choices',
            'field_order'])

        for attribute in query:
            schema = attribute.schema
            choices = attribute.choices
            writer.writerow([
                schema.name,
                schema.title,
                schema.publish_date,
                attribute.name,
                attribute.title,
                attribute.description,
                attribute.is_required,
                attribute.is_collection,
                attribute.type,
                '\r'.join(['%s - %s' % (c.name, c.title) for c in choices]),
                attribute.order])

        tfp.flush() # ensure everything's on disk
        zfp.write(tfp.name, arcname)

