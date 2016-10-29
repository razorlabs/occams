"""
Contains long-running tasks that cannot interrupt the user experience.

Tasks in this module will be run in a separate process so the user
can continue to use the application and download their exports at a
later time.
"""

from __future__ import absolute_import

try:
    import unicodecsv as csv
except ImportError:  # pragma: nocover
    import csv  # NOQA (py3, hopefully)
try:
    from collections import OrderedDict
except ImportError:  # pragma: nocover
    from ordereddict import OrderedDict  # NOQA
from contextlib import closing
from itertools import chain
import json
import os
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED

import celery.signals
import humanize
import six

from occams.celery import app, Session, log, with_transaction

from . import models, exports


def includeme(config):
    """
    Configures the Celery connection from the pyramid side of the application.

    Pyramid must know how to talk to the celery process in order to send
    asynchronous jobs.

    This method will not actually start the celery process.

    :param config: Pyramid configuration object

    """

    settings = config.registry.settings

    settings['studies.export.dir'] = \
        os.path.abspath(settings['studies.export.dir'])
    assert os.path.exists(settings['studies.export.dir']), \
        'Does not exist: %s' % settings['studies.export.dir']

    if 'studies.export.limit' in settings:
        settings['studies.export.limit'] = \
            int(settings['studies.export.limit'])

    if 'studies.export.expire' in settings:
        settings['studies.export.expire'] = \
            int(settings['studies.export.expire'])


@celery.signals.celeryd_after_setup.connect
def on_celeryd_after_setup(**kw):
    """
    Triggers initial processes when the Celery daemon completes its setup
    """

    # Make a codebook immediately (beat will wait UNTIL AFTER the specified
    # amount of time, which is bad if we need and initial file right away)
    make_codebook.apply_async()


class ExportTask(celery.Task):

    abstract = True

    @with_transaction
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        log.error('Task {0} raised exception: {1!r}\n{2!r}'.format(
                  task_id, exc, einfo))

        export = Session.query(models.Export).filter_by(name=task_id).one()
        export.status = u'failed'

        redis = app.redis
        redis.hset(export.redis_key, 'status', export.status)
        redis.publish('export', json.dumps(redis.hgetall(export.redis_key)))


@celery.task(name='make_export', base=ExportTask, ignore_result=True)
@with_transaction
def make_export(name):
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

    redis = app.redis

    export = Session.query(models.Export).filter_by(name=name).one()

    redis.hmset(export.redis_key, {
        'export_id': export.id,
        'owner_user': export.owner_user.key,
        'status': export.status,
        'count': 0,
        'total': len(export.contents),
    })

    with closing(ZipFile(export.path, 'w', ZIP_DEFLATED)) as zfp:

        exportables = exports.list_all(Session)

        for item in export.contents:
            plan = exportables[item['name']]

            with tempfile.NamedTemporaryFile() as tfp:
                exports.write_data(tfp, plan.data(
                    use_choice_labels=export.use_choice_labels,
                    expand_collections=export.expand_collections))
                zfp.write(tfp.name, plan.file_name)

            redis.hincrby(export.redis_key, 'count')
            data = redis.hgetall(export.redis_key)
            # redis-py returns everything as string, so we need to clean it
            for key in ('export_id', 'count', 'total'):
                data[key] = int(data[key])
            redis.publish('export', json.dumps(data))
            count, total = data['count'], data['total']
            log.info(', '.join(map(str, [count, total, item['name']])))

        with tempfile.NamedTemporaryFile() as tfp:
            codebook_chain = \
                [p.codebook() for p in six.itervalues(exportables)]
            exports.write_codebook(tfp, chain.from_iterable(codebook_chain))
            zfp.write(tfp.name, exports.codebook.FILE_NAME)

    export.status = 'complete'
    redis.hmset(export.redis_key, {
        'status': export.status,
        'file_size': humanize.naturalsize(export.file_size)
    })
    redis.publish('export', json.dumps(redis.hgetall(export.redis_key)))


@celery.task(name='make_codebook', ignore_result=True, bind=True)
@with_transaction
def make_codebook(task):
    """
    Pre-cooks a codebook file for faster downloading
    """
    try:
        codebook_chain = \
            [p.codebook() for p in six.itervalues(exports.list_all(Session))]
        path = os.path.join(app.settings['studies.export.dir'],
                            exports.codebook.FILE_NAME)
        with open(path, 'w+b') as fp:
            exports.write_codebook(fp, chain.from_iterable(codebook_chain))
    except Exception as exc:
        # Need to keep retrying (default is every 3 min)
        task.retry(exc=exc)
