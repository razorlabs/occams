from pkg_resources import resource_filename

from pyramid.settings import asbool
from webassets import Bundle
from webassets.loaders import PythonLoader


def config_assets(config):
    """
    Loads web assets
    """
    env = config.get_webassets_env()

    # Third-Party libraries

    config.add_webasset('jquery', Bundle('scripts/jquery.min.js'))
    config.add_webasset('bootstrap_js', Bundle('scripts/bootstrap.min.js'))
    config.add_webasset('bootstrap_css', Bundle('styles/bootstrap.min.css'))

    # Default

    config.add_webasset('default_css', Bundle(
        env['bootstrap_css'],
        'styles/stickynavfoot.css',
        'styles/login.css',
        filters='cssmin',
        output='gen/default.%(version)s.css'))

    config.add_webasset('default_js', Bundle(
        env['jquery'],
        env['bootstrap_js'],
        'scripts/lib.selectall.js',
        filters='jsmin',
        output='gen/default.%(version)s.js'))

    return config



