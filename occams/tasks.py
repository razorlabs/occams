"""
Contains long-running tasks that cannot interrupt the user experience.

Tasks in this module will be run in a separate process so the user
can continue to use the application and download their exports at a
later time.
"""

import csv
from collections import OrderedDict
from datetime import timedelta
from itertools import chain
import json
import os
import tempfile
from urllib.parse import urlparse
from zipfile import ZipFile, ZIP_DEFLATED

from celery import Celery, bootsteps, signals, Task
from celery.bin import Option
from celery.utils.log import get_task_logger
from pyramid.settings import aslist
from pyramid.paster import get_appsettings
import humanize
from redis import Redis
import sqlalchemy as sa
from sqlalchemy import orm

from . import models, exports


class IniConfigLoader(bootsteps.Step):
    """
    Configures Celery in the worker process
    """

    def __init__(self, worker, ini, **options):
        settings = get_appsettings(ini[0])
        configure(settings)


app = Celery(__name__)
app.user_options['worker'].add(Option('--ini', help='Pyramid config file'))
app.steps['worker'].add(IniConfigLoader)

log = get_task_logger(__name__)


def includeme(config):
    """
    Configures the Celery connection from the pyramid side of the application.

    Pyramid must know how to talk to the celery process in order to send
    asynchronous jobs.

    This method will not actually start the celery process.

    :param config: Pyramid configuration object

    """

    configure(config.registry.settings)


def configure(settings):
    """
    Common configurator for both the Celery worker and the web application
    """
    assert 'celery.blame' in settings, 'Must specify an blame user'

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

    app.conf.update(
        broker_url=settings['celery.broker.url'],
        result_backend=settings['celery.backend.url'],
        broker_transport_options={
            'fanout_prefix': True,
            'fanout_patterns': True
        },
        imports=aslist(settings.get('celery.include', [])),
        beat_schedule=_get_schedule(settings)
    )

    # OCCAMS-specific settings
    app.conf.settings = settings


def _get_schedule(settings):
    """
    Schedule parser if configuration specifies celery-beat operations
    """
    schedule = {}

    beats = aslist(settings.get('celery.beat', []))

    if not beats:
        return None

    def maybeint(value):
        try:
            return int(value)
        except:
            return None

    timedelta_params = [
        'days', 'seconds', 'microseconds', 'milliseconds',
        'minutes', 'hours', 'weeks']

    for beat in beats:

        task = settings.get('celery.beat.{}.task'.format(beat))
        assert task, 'No task specified for beat: {}'.format(beat)

        schedule_type = settings.get('celery.beat.{}.schedule'.format(beat))
        assert schedule_type, \
            'No schedule type specified for beat: {}'.format(beat)

        if schedule_type == 'timedelta':
            params = {}
            for param in timedelta_params:
                setting_key = 'celery.beat.{}.schedule.{}'.format(beat, param)
                value = maybeint(settings.get(setting_key))
                if value:
                    params[param] = value
            beat_schedule = timedelta(**params)
        else:
            raise Exception(
                'Unsupported schedule type: {}'.format(schedule_type))

        schedule[beat] = {
            'task': task,
            'schedule': beat_schedule,
        }

    return schedule


def with_transaction(func):
    """
    Function decoratator that commits on successul execution, aborts otherwise.
    Also releases connection to prevent leaked open connections.
    """
    def decorated(*args, **kw):
        task, *_ = args
        userid = task.app.conf.settings['celery.blame']
        dbsession = task.dbsession
        dbsession.execute(
            sa.text('SET LOCAL "application.name" = :param'),
            {'param': 'celery'}
        )
        dbsession.execute(
            sa.text('SET LOCAL "application.user" = :param'),
            {'param': userid}
        )
        try:
            result = func(*args, **kw)
            dbsession.commit()
        except:
            dbsession.rollback()
            raise
        finally:
            dbsession.remove()
        return result
    return decorated


class OccamsTask(Task):
    """
    Application-specific Task class that instantiates necessary resources

    See: https://docs.celeryproject.org/en/stable/userguide/tasks.html#custom-task-classes
    """

    _dbsession = None
    _redis = None

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        if (self._dbsession):
            # Ensure db connection is cleaned up after the task completes
            self._dbsession.remove()

    @property
    def dbsession(self):
        """
        Thread-local database session
        """
        if self._dbsession is None:
            settings = self.app.conf.settings
            dbsession = orm.scoped_session(orm.sessionmaker())
            engine = sa.create_engine(settings['sqlalchemy.url'])
            dbsession.configure(
                bind=engine,
                info={'settings': settings}
            )
            self._dbsession = dbsession
        return self._dbsession

    @property
    def redis(self):
        """
        Redis connection to publish events
        """
        if self._redis is None:
            settings = self.app.conf.settings
            redisurl = urlparse(settings['redis.url'])
            redis = Redis(
                host=redisurl.hostname,
                port=redisurl.port,
                db=os.path.basename(redisurl.path),
                decode_responses=True
            )
            self._redis = redis
        return self._redis


@with_transaction
def on_failure_make_export(self, exc, task_id, args, kwargs, einfo):
    """
    Error handler for `make_export` task.
    Marks the export as failed dispatches failure to listening applications.
    """
    dbsession = self.dbsession
    redis = self.redis

    log.error('Task {0} raised exception: {1!r}\n{2!r}'.format(
              task_id, exc, einfo))

    export = dbsession.query(models.Export).filter_by(name=task_id).one()
    export.status = u'failed'

    redis.hset(export.redis_key, 'status', export.status)
    redis.publish('export', json.dumps(redis.hgetall(export.redis_key)))


@app.task(
    name='make_export',
    base=OccamsTask,
    bind=True,
    ignore_result=True,
    on_failure=on_failure_make_export
)
@with_transaction
def make_export(self, name):
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

    redis = self.redis
    dbsession = self.dbsession

    export = dbsession.query(models.Export).filter_by(name=name).one()

    redis.hmset(export.redis_key, {
        'export_id': export.id,
        'owner_user': export.owner_user.key,
        'status': export.status,
        'count': 0,
        'total': len(export.contents),
    })

    with ZipFile(export.path, mode='w', compression=ZIP_DEFLATED) as zfp:
        exportables = exports.list_all(dbsession)

        for item in export.contents:
            plan = exportables[item['name']]

            with tempfile.NamedTemporaryFile(mode='w') as tfp:
                exports.write_data(tfp, plan.data(
                    use_choice_labels=export.use_choice_labels,
                    expand_collections=export.expand_collections))
                zfp.write(tfp.name, plan.file_name)

            redis.hincrby(export.redis_key, 'count')
            data = redis.hgetall(export.redis_key)
            redis.publish('export', json.dumps(data))

            count, total, name = data['count'], data['total'], item['name']
            log.info(f'{count} of {total}: {name}')

        with tempfile.NamedTemporaryFile(mode='w') as tfp:
            codebook_chain = \
                [p.codebook() for p in exportables.values()]
            exports.write_codebook(tfp, chain.from_iterable(codebook_chain))
            zfp.write(tfp.name, exports.codebook.FILE_NAME)

    export.status = 'complete'
    redis.hmset(export.redis_key, {
        'status': export.status,
        'file_size': humanize.naturalsize(export.file_size)
    })
    redis.publish('export', json.dumps(redis.hgetall(export.redis_key)))


@app.task(name='make_codebook', base=OccamsTask, ignore_result=True, bind=True)
def make_codebook(self):
    """
    Creates a coodebook file that is ready to be served on demand by the web app
    """
    dbsession = self.dbsession
    export_dir= self.app.conf.settings['studies.export.dir']
    try:
        codebook_chain = \
            [p.codebook() for p in exports.list_all(dbsession).values()]
        path = os.path.join(export_dir, exports.codebook.FILE_NAME)
        with open(path, 'w') as fp:
            exports.write_codebook(fp, chain.from_iterable(codebook_chain))
    except Exception as exc:
        # Need to keep retrying (default is every 3 min)
        self.retry(exc=exc)


@signals.celeryd_after_setup.connect
def on_celeryd_after_setup(**kw):
    """
    Triggers initial processes when the Celery daemon completes its setup
    """

    # Generate codebook on startup in case it's needed ASAP
    make_codebook.apply_async()
