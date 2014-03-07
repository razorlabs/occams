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
from itertools import chain
import json
import os

from celery import Task
import humanize

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
        export = Session.query(models.Export).filter_by(task_id=task_id).one()
        export.status = 'failed'
        Session.flush()
        redis.hset(export.redis_key, 'status', export.status)
        redis.publish('export', json.dumps(redis.hgetall(export.redis_key)))


@app.task(name='make_export', base=ExportTask, ignore_result=True)
@in_transaction
def make_export(task_id):
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
    export = Session.query(models.Export).filter_by(task_id=task_id).one()

    redis = app.redis

    redis.hmset(export.redis_key, {
        'export_id': export.id,
        'owner_user': export.owner_user.key,
        'status': export.status,
        'count': 0,
        'total': len(export.contents)})

    exportables = reports.list_all()

    path = os.path.join(app.settings['app.export.dir'], export.path)
    os.makedirs(path)

    codebook_chain = []

    for item in export.contents:

        with open(os.path.join(path, item['name'] + '.csv'), 'w+b') as fp:
            report = exportables[item['name']]
            data = report.data()
            codebook = report.codebook()
            codebook_chain.append(codebook)
            reports.write_data(fp, data)

        redis.hincrby(export.redis_key, 'count')
        redis.publish('export', json.dumps(redis.hgetall(export.redis_key)))
        count, total = redis.hmget(export.redis_key, 'count', 'total')
        log.info(', '.join([count, total, item['name']]))

    with open(os.path.join(path, 'codebook.csv'), 'w+b') as fp:
        reports.write_codebook(fp, chain.from_iterable(codebook_chain))
        log.info('codebook')

    export.status = 'complete'
    redis.hset(export.redis_key, 'status', export.status)
    redis.hset(export.redis_key, 'file_size',
               humanize.naturalsize(os.path.getsize(path)))

    Session.flush()  # flush so we know everything went smoothly
    redis.publish('export', json.dumps(redis.hgetall(export.redis_key)))
