import json


def includeme(config):
    """
    Configures application links
    """
    file = config.registry.settings.get('suite.file')
    if file:
        with open(file) as fp:
            apps = json.load(fp)
            config.add_request_method(lambda r: apps, name='apps', reify=True)
