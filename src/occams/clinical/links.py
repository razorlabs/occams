try:
    import configparser
except ImportError:
    import ConfigParser as configparser

from occams.clinical import log


def includeme(config):
    log.debug('Loadings apps listing...')
    settings = config.registry.settings
    apps = make_app_listing(settings.get('apps.config_file'))
    config.add_request_method(lambda r: apps, name='apps', reify=True)


def make_app_listing(file_name):
    """
    Generates a listing of additional services as specified in the config file.

    Parameters:
    file_name -- The config file specifing external services

    Returns:
    A listing of dictionaries.
    """
    listing = []

    if not file_name:
        return listing

    config = configparser.SafeConfigParser()
    config.read(file_name)

    if not config.has_section('main'):
        return listing

    for suite_name in config.get('main', 'suites').split():
        suite_section = 'suite:' + suite_name
        suite = {
            'name': suite_name,
            'title': config.get(suite_section, 'title'),
            'apps': [],
            }
        for app_name in config.get(suite_section, 'apps').split():
            app_section = 'app:' + app_name
            app = {
                'name': app_name,
                'title': config.get(app_section, 'title'),
                'url': config.get(app_section, 'url')}
            suite['apps'].append(app)
        listing.append(suite)

    return listing
