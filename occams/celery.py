"""
Contains long-running tasks that cannot interrupt the user experience.

Tasks in this module will be run in a separate process so the user
can continue to use the application and download their exports at a
later time.
"""

from __future__ import absolute_import

from datetime import timedelta
import os

from celery import Celery
from celery.bin import Option
import celery.signals
from celery.utils.log import get_task_logger
import six
from pyramid.settings import aslist
from pyramid.paster import bootstrap
import redis
import sqlalchemy as sa
from sqlalchemy import orm

from . import models
from .models.events import register


app = Celery(__name__)

app.user_options['preload'].add(
    Option('--ini', help='Pyramid config file')
)

log = get_task_logger(__name__)

#
# Dedicated Celery application database session.
# DO NOT USE THIS SESSION IN THE WSGI APP
#
# TODO: Haven't figured out how to make this a non-global variable for
#       celery tasks...
#
Session = orm.scoped_session(orm.sessionmaker())
register(Session)


def includeme(config):
    """
    Configures the Celery connection from the pyramid side of the application.

    Pyramid must know how to talk to the celery process in order to send
    asynchronous jobs.

    This method will not actually start the celery process.

    :param config: Pyramid configuration object

    """
    settings = config.registry.settings

    assert 'celery.blame' in settings, 'Must specify an blame user'

    app.conf.update(
        BROKER_URL=settings['celery.broker.url'],
        CELERY_RESULT_BACKEND=settings['celery.backend.url'],
        BROKER_TRANSPORT_OPTIONS={
            'fanout_prefix': True,
            'fanout_patterns': True
        },
        CELERY_INCLUDE=aslist(settings.get('celery.include', [])),
        CELERYBEAT_SCHEDULE=_get_schedule(settings)
    )

    app.settings = settings


def _get_schedule(settings):
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


@celery.signals.user_preload_options.connect
def on_preload_parsed(options, **kw):
    """
    Called when the main Celery process parses a configuration file
    """
    # Have the pyramid app initialize all settings
    # We need to load th actual application since it evaluates all the
    # settings, it *should* not interfere with any threadlocal stuff
    # (hence the closer call)
    env = bootstrap(options['ini'])
    env['closer']()
    del env


@celery.signals.celeryd_init.connect
def on_celeryd_init(**kw):
    """
    Initializes application resources when the Celery daeomon starts
    """
    settings = app.settings

    redisurl = six.moves.urllib.parse.urlparse(settings['redis.url'])
    app.redis = redis.StrictRedis(
        host=redisurl.hostname,
        port=redisurl.port,
        db=os.path.basename(redisurl.path)
    )

    app.userid = settings['celery.blame']

    # Attempt to add the user via raw engine connection, using the scoped
    # session leaves it in a dangerous non-thread-local state as we're
    # still in the parent setup process
    throw_away_engine = sa.engine_from_config(settings)
    with throw_away_engine.begin() as connection:
        try:
            connection.execute(models.User.__table__.insert(),  key=app.userid)
        except sa.exc.IntegrityError:
            pass
    throw_away_engine.dispose()

    # Configure the session with an untainted engine
    engine = sa.engine_from_config(settings)
    Session.configure(bind=engine)


def with_transaction(func):
    """
    Function decoratator that commits on successul execution, aborts otherwise.

    Also releases connection to prevent leaked open connections.
    """
    def decorated(*args, **kw):
        userid = app.userid
        Session.info['blame'] = (
            Session.query(models.User)
            .filter_by(key=userid)
            .one())
        Session.info['settings'] = app.settings
        try:
            result = func(*args, **kw)
            Session.commit()
        except:
            Session.rollback()
            raise
        finally:
            Session.remove()
        return result
    return decorated
