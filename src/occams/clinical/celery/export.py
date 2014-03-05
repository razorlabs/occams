"""
Contains long-running tasks that cannot interrupt the user experience.

Tasks in this module will be run in a separate process so the user
can continue to use the application and download their exports at a
later time.
"""

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict  # NOQA
from contextlib import closing
import json
import os
import tempfile
import zipfile

from celery import Task
import humanize
from webob.multidict import MultiDict

from occams.clinical import models, Session
from occams.clinical.celery import app, log, in_transaction
from occams.clinical import reports


class ExportTask(Task):

    abstract = True

    @in_transaction
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        log.error('Task {0} raised exception: {1!r}\n{2!r}'.format(
                  task_id, exc, einfo))
        redis = app.redis
        export_id, = args
        export = Session.query(models.Export).filter_by(id=export_id).one()
        export.status = 'failed'
        Session.flush()
        redis.hset(export_id, 'status', export.status)
        redis.publish('export', json.dumps(redis.hgetall(export_id)))


@app.task(name='make_export', base=ExportTask, ignore_result=True)
@in_transaction
def make_export(export_id):
    """
    Handles generating exports in a separate process.

    Because the export is handled in a different process, this method
    can only accept the id of the entry. This is to avoid race
    conditions,
    (http://docs.celeryproject.org/en/latest/userguide/tasks.html#state)

    All progress will be broadcast to the redis **export** channel with the
    following dictionary:
    export_id -- the export being processed
    owner_user -- the user who this export belongs to
    count -- the current number of files processed
    total -- the total number of files that will be processed
    status -- current status of the export

    Parameters:
    export_id -- export to process

    """
    export = Session.query(models.Export).filter_by(id=export_id).one()

    # Organize the forms so we know which schemata go where
    files = MultiDict([(s.name, s.id) for s in export.schemata])

    redis = app.redis

    redis.hmset(export.id, {
        'export_id': export.id,
        'owner_user': export.owner_user.key,
        'status': export.status,
        'count': 0,
        'total': len(set(files.keys()))})

    path = os.path.join(app.settings['app.export.dir'], export.name)

    with closing(zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED)) as zfp:
        for schema_name, ids in files.dict_of_lists().items():

            with tempfile.NamedTemporaryFile() as tfp:
                query = reports.form.query_report(
                    schema_name,
                    ids,
                    expand_collections=export.expand_collections,
                    use_choice_labels=export.use_choice_labels)
                reports.io.query2csv(query, tfp)
                zfp.write(tfp.name, '{0}.csv'.format(schema_name))

            with tempfile.NamedTemporaryFile() as tfp:
                rows = reports.form.codebook(schema_name, ids)
                reports.io.codebook2csv(rows)
                zfp.write(tfp.name, '{0}-codebook.csv'.format(schema_name))

            redis.hincrby(export.id, 'count')
            redis.publish('export', json.dumps(redis.hgetall(export.id)))
            count, total = redis.hmget(export.id, 'count', 'total')
            log.info(', '.join([count, total, schema_name]))

    export.status = 'complete'
    redis.hset(export_id, 'status', export.status)
    redis.hset(export_id, 'file_size',
               humanize.naturalsize(os.path.getsize(path)))

    Session.flush()  # flush so we know everything went smoothly
    redis.publish('export', json.dumps(redis.hgetall(export_id)))
