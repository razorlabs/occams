import json

from . import log


def includeme(config):
    try:
        with open(config.registry.settings.get('suite.file')) as fp:
            apps = json.load(fp)
    except TypeError:
        log.debug('No suite file found')
        apps = None
    except IOError:
        log.debug('Could not read suite file')
        apps = None
    config.add_request_method(lambda r: apps, name='apps', reify=True)
    log.debug('External app listing configured.')
