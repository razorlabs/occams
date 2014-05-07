"""
Contains long-running tasks that cannot interrupt the user experience.

Tasks in this module will be run in a separate process so the user
can continue to use the application and download their exports at a
later time.
"""

try:
    import unicodecsv as csv
except ImportError:  # pragma: nocover
    import csv  # NOQA (py3, hopefully)
try:
    from collections import OrderedDict
except ImportError:  # pragma: nocover
    from ordereddict import OrderedDict  # NOQA
from contextlib import closing
from datetime import timedelta
from itertools import chain
import json
import os
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED

from celery import Celery, Task
from celery.bin import Option
from celery.signals import user_preload_options, worker_init
from celery.utils.log import get_task_logger
import humanize
from six import itervalues
from pyramid.paster import bootstrap
from sqlalchemy.orm.exc import NoResultFound
import transaction

from . import models, Session, exports
from .security import track_user


celery = Celery(__name__)

celery.user_options['preload'].add(
    Option('--ini', help='Pyramid config file')
)


log = get_task_logger(__name__)


def includeme(config):
    settings = config.registry.settings

    assert 'app.export.user' in settings, 'Must specify an export user'

    settings['app.export.dir'] = os.path.abspath(settings['app.export.dir'])
    assert os.path.exists(settings['app.export.dir']), \
        'Does not exist: %s' % settings['app.export.dir']

    if 'app.export.limit' in settings:
        settings['app.export.limit'] = int(settings['app.export.limit'])

    if 'app.export.expire' in settings:
        settings['app.export.expire'] = int(settings['app.export.expire'])

    celery.conf.update(
        BROKER_URL=settings['celery.broker.url'],
        CELERY_RESULT_BACKEND=settings['celery.backend.url'],
        BROKER_TRANSPORT_OPTIONS={
            'fanout_prefix': True,
            'fanout_patterns': True
        },
        CELERYBEAT_SCHEDULE={
            'make-codebook-every-hour': {
                'task': 'make_codebook',
                'schedule': timedelta(hours=1),
            },
        })


@user_preload_options.connect
def on_preload_parsed(options, **kwargs):
    """
    Use Pyramid applicaiton settings  for all types of celery commands
    """
    # Have the pyramid app initialize all settings
    env = bootstrap(options['ini'] + '#occams.studies')

    # Setup resources for tasks
    celery.settings = env['registry'].settings
    celery.redis = env['request'].redis


@worker_init.connect
def worker_init_handler(signal, sender):
    """
    Initialize database for worker processes
    """

    userid = sender.app.settings['app.export.user']

    with transaction.manager:
        track_user(userid)

    # Clear the registry so we ALWAYS get the correct userid
    Session.remove()
    Session.configure(info={'user': userid})

    # Make a codebook immediately (beat will wait UNTIL AFTER the specified
    # amount of time, which is bad if we need and initial file right away)
    make_codebook.apply_async()


def in_transaction(func):
    """
    Function decoratator that commits on successul execution, aborts otherwise.

    Also releases connection to prevent leaked open connections.

    The pyramid application-portion relies on ``pyramid_tm`` to commit at
    the end of each request. Tasks don't have this luxury and must
    be committed manually after each successful call.
    """
    def decorated(*args, **kw):
        with transaction.manager:
            result = func(*args, **kw)
        Session.remove()
        return result
    return decorated


class ExportTask(Task):

    abstract = True

    @in_transaction
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        log.error('Task {0} raised exception: {1!r}\n{2!r}'.format(
                  task_id, exc, einfo))
        redis = celery.redis
        export = Session.query(models.Export).filter_by(name=task_id).one()
        export.status = u'failed'
        Session.flush()
        redis.hset(export.redis_key, 'status', export.status)
        redis.publish('export', json.dumps(redis.hgetall(export.redis_key)))

    @in_transaction
    def on_success(self, retval, task_id, args, kwargs):
        try:
            export = Session.query(models.Export).filter_by(name=task_id).one()
        except NoResultFound:
            # Assume revoked
            return
        export.status = 'complete'
        redis = celery.redis
        redis.hmset(export.redis_key, {
            'status': export.status,
            'file_size': humanize.naturalsize(export.file_size)
        })
        Session.flush()
        redis.publish('export', json.dumps(redis.hgetall(export.redis_key)))


@celery.task(name='make_export', base=ExportTask, ignore_result=True)
@in_transaction
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
    export = Session.query(models.Export).filter_by(name=name).one()

    redis = celery.redis

    redis.hmset(export.redis_key, {
        'export_id': export.id,
        'owner_user': export.owner_user.key,
        'status': export.status,
        'count': 0,
        'total': len(export.contents)
    })

    with closing(ZipFile(export.path, 'w', ZIP_DEFLATED)) as zfp:

        exportables = exports.list_all()

        for item in export.contents:
            plan = exportables[item['name']]

            with tempfile.NamedTemporaryFile() as tfp:
                exports.write_data(tfp, plan.data(
                    use_choice_labels=export.use_choice_labels,
                    expand_collections=export.expand_collections))
                zfp.write(tfp.name, plan.file_name)

            redis.hincrby(export.redis_key, 'count')
            message = json.dumps(redis.hgetall(export.redis_key))
            redis.publish('export', message)
            count, total = redis.hmget(export.redis_key, 'count', 'total')
            log.info(', '.join([count, total, item['name']]))

        with tempfile.NamedTemporaryFile() as tfp:
            codebook_chain = [p.codebook() for p in itervalues(exportables)]
            exports.write_codebook(tfp, chain.from_iterable(codebook_chain))
            zfp.write(tfp.name, exports.codebook.FILE_NAME)


@celery.task(name='make_codebook', ignore_result=True)
@in_transaction
def make_codebook():
    """
    Pre-cooks a codebook file for faster downloading
    """
    codebook_chain = [p.codebook() for p in itervalues(exports.list_all())]
    path = os.path.join(celery.settings['app.export.dir'],
                        exports.codebook.FILE_NAME)
    with open(path, 'w+b') as fp:
        exports.write_codebook(fp, chain.from_iterable(codebook_chain))
