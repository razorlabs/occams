"""
Contains long-running tasks that cannot interrupt the user experience.

Tasks in this module will be run in a separate process so the user
can continue to use the application and download their exports at a
later time.
"""

from contextlib import closing
import csv
import json
import os.path
import tempfile
import zipfile
from pkg_resources import resource_filename

import celery

from occams.datastore import model as datastore, reporting

from . import models, Session, redis


@celery.task
def make_export(export_id):
    """
    Handles generating exports in a separate process.

    Because the export is handled in a different process, this method
    can only accept the id of the entry.

    All progress will be broadcast to the redis **export** channel with the
    following dictionary:
    ``export_id`` -- the export being processed
    ``owner_user`` -- the user who this export belongs to
    ``progress`` -- the percent complete
    ``is_ready`` -- flag that indicates that the export can be used

    Parameters:
    ``export_id`` -- export to process

    """
    # Get the export instance attached to this thread
    export = Session.query(models.Export).get(export_id)

    export_dir = resource_filename('occams.clinical', 'exports')
    path = os.path.join(export_dir, '%s.zip' % export.id)

    total = float(len(export.items))

    redis.hmset(export.id, {
        'export_id': export.id,
        'owner_user': export.owner_user.key,
        'status': export.status,
        'progress': 0})
    redis.publish('export', json.dumps(redis.hgetall(export.id)))

    with closing(zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED)) as zfp:
        for count, item in enumerate(export.items, start=1):
            if item.table_name:
                arcname = item.table_name
                cols = models.BUILTINS[item.table_name]
                query = Session.query(*cols).order_by(cols[0])
                dump_table_datadict(zfp, arcname + 'datadict.csv', query)
            else:
                ecrf = item.schema
                arcname = ecrf.name + '-' + str(ecrf.publish_date)
                query = Session.query(reporting.export(ecrf))

            with tempfile.NamedTemporaryFile() as tfp:
                writer = csv.writer(tfp)
                writer.writerow([d['name'] for d in query.column_descriptions])
                writer.writerows(query)
                tfp.flush()
                zfp.write(tfp.name, arcname + '.csv')

            progress = int((count / total) * 100)

            # celery treats ``print` statements as log messages
            print(arcname, progress)

            redis.hset(export_id, 'progress', progress)
            redis.publish('export', json.dumps(redis.hgetall(export.id)))

    # File has been closed/flushed, it's ready for consumption
    export.status = 'complete'
    Session.commit()
    redis.hset(export_id, 'status', export.status)
    redis.publish('export', json.dumps(redis.hgetall(export.id)))


@celery.task
def cleanup_export(expire_date):
    """
    Cleans up the database of expired exports.

    Parameters:
    ``expire_date`` -- the cut-off date for removal
    """
    raise NotImplementedError


def dump_table_datadict(zfp, arcname, query):
    pass


def dump_ecrf_datadict(zfp, arcname, query):
    pass

