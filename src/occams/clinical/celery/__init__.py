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
except ImportError:
    from ordereddict import OrderedDict  # NOQA

from celery import Celery
from celery.bin import Option
from celery.signals import worker_init
from celery.utils.log import get_task_logger
from pyramid.paster import bootstrap
import transaction

from occams.clinical import Session
from occams.clinical.auth import track_user
from occams.clinical.utils.pkg import resolve_path
from occams.clinical.utils.types import cast_maybe


app = Celery(
    __name__,
    includes=['occams.clinical.celery.export'])

app.user_options['worker'].add(
    Option('--ini', help='Pyramid config file'))

log = get_task_logger(__name__)


def includeme(config):
    settings = config.registry.settings

    assert 'app.export.user' in settings, 'Must specify an export user'

    settings['app.export.dir'] = \
        resolve_path(settings['app.export.dir'], validate=True)

    settings['app.export.limit'] = \
        cast_maybe(settings.get('app.export.limit'), int)
    settings['app.export.expire'] = \
        cast_maybe(settings.get('app.export.expire'), int)


@worker_init.connect
def init(signal, sender):
    """
    Configure the database connections when the celery daemon starts
    """
    # Have the pyramid app initialize all settings
    env = bootstrap(sender.options['ini'])
    sender.app.settings = settings = env['registry'].settings
    sender.app.redis = env['request'].redis

    userid = settings['app.export.user']

    with transaction.manager:
        track_user(userid)

    # Clear the registry so we ALWAYS get the correct userid
    Session.remove()
    Session.configure(info={'user': userid})

    sender.app.conf.update(
        BROKER_URL=settings['celery.broker.url'])


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
