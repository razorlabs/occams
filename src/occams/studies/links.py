import json

from . import log


def includeme(config):
    file = config.registry.settings.get('suite.file')

    if file:
        with open(file) as fp:
            apps = json.load(fp)
    else:
        apps = None

    def callback(request):
        return apps

    config.add_request_method(callback, name='apps', reify=True)
    log.debug('External app listing configured.')
